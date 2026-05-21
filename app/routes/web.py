# ==================================================
# app/routes/web.py
# FINAL PROFESSIONAL VERSION
# ==================================================

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user,
    logout_user
)

from datetime import datetime, timezone
import re

# ==================================================
# DATABASE + MODELS
# ==================================================
from app.extensions import db

from app.models.product import Product
from app.models.product_link import ProductLink
from app.models.price_history import PriceHistory
from app.models.tracked_product import TrackedProduct
from app.models.alert import Alert

# ==================================================
# SCRAPERS
# ==================================================
from app.scrapers.base_scraper import search_all_sites
from app.scrapers.url_scraper import scrape_from_url

# ==================================================
# LOGGER
# ==================================================
from app.utils.log_activity import log_activity

# ==================================================
# BLUEPRINT
# ==================================================
web = Blueprint("web", __name__)


# ==================================================
# HOME PAGE
# ==================================================
@web.route("/")
def home():

    return render_template("auth/index.html")


# ==================================================
# DASHBOARD
# ==================================================
@web.route("/dashboard")
@login_required
def dashboard():

    tracked_items = (
        TrackedProduct.query
        .filter_by(user_id=current_user.id)
        .order_by(TrackedProduct.id.desc())
        .all()
    )

    return render_template(
        "user/dashboard.html",
        user=current_user,
        products=tracked_items
    )


# ==================================================
# HISTORY PAGE
# ==================================================
@web.route("/history")
@login_required
def history():

    products = (
        TrackedProduct.query
        .filter_by(user_id=current_user.id)
        .order_by(TrackedProduct.id.desc())
        .all()
    )

    return render_template(
        "user/history.html",
        products=products
    )


# ==================================================
# ALERTS PAGE
# ==================================================
@web.route("/alerts")
@login_required
def alerts():

    alerts = (
        Alert.query
        .filter_by(user_id=current_user.id)
        .order_by(Alert.id.desc())
        .all()
    )

    return render_template(
        "user/alerts.html",
        alerts=alerts
    )


# ==================================================
# SAVED PRODUCTS
# ==================================================
@web.route("/saved")
@login_required
def saved():

    items = (
        TrackedProduct.query
        .filter_by(user_id=current_user.id)
        .order_by(TrackedProduct.id.desc())
        .all()
    )

    return render_template(
        "user/saved.html",
        items=items
    )


# ==================================================
# SETTINGS
# ==================================================
@web.route("/settings")
@login_required
def settings():

    return render_template("user/settings.html")


# ==================================================
# SHOP PAGE
# ==================================================
@web.route("/shop")
@login_required
def shop():

    query = request.args.get("q", "").strip()

    return render_template(
        "user/search_product.html",
        results=[],
        query=query
    )


# ==================================================
# SEARCH PRODUCTS
# ==================================================
@web.route("/search", methods=["GET"])
@login_required
def search_page():

    query = request.args.get("q", "").strip()

    if not query:

        flash(
            "Please enter a search query.",
            "warning"
        )

        return redirect(url_for("web.shop"))

    results = []

    try:

        # ==================================================
        # URL SEARCH MODE
        # ==================================================
        if (
            query.startswith("http://")
            or query.startswith("https://")
        ):

            clean_url = query.split("?")[0]

            # REMOVE AMAZON REF PART
            if "/ref=" in clean_url:
                clean_url = clean_url.split("/ref=")[0]

            # AMAZON CLEAN URL
            if "amazon." in clean_url:

                asin_match = re.search(
                    r"/(?:dp|gp/product)/([A-Z0-9]{10})",
                    clean_url
                )

                if asin_match:

                    asin = asin_match.group(1)

                    clean_url = (
                        f"https://www.amazon.in/dp/{asin}"
                    )

            print("CLEAN URL:", clean_url)

            product = scrape_from_url(clean_url)

            if product and product.get("price", 0) > 0:

                results = [product]

            else:

                flash(
                    "Could not scrape product.",
                    "danger"
                )

        # ==================================================
        # NORMAL TEXT SEARCH
        # ==================================================
        else:

            results = search_all_sites(query)

        # ==================================================
        # REMOVE BAD RESULTS
        # ==================================================
        cleaned = []

        for item in results:

            if not isinstance(item, dict):
                continue

            if item.get("price", 0) <= 0:
                continue

            if item.get("title", "N/A") == "N/A":
                continue

            cleaned.append(item)

        results = cleaned

        log_activity(f"Searched: {query}")

    except Exception as e:

        print("SEARCH ERROR:", e)

        flash(
            "Search failed.",
            "danger"
        )

    return render_template(
        "user/search_product.html",
        query=query,
        results=results
    )


# ==================================================
# TRACK PRODUCT
# ==================================================
@web.route("/track-product", methods=["POST"])
@login_required
def track_product_route():

    try:

        # ==================================================
        # FORM DATA
        # ==================================================
        name = request.form.get("name", "").strip()

        price = float(
            request.form.get("price") or 0
        )

        website = request.form.get(
            "website",
            "Unknown"
        ).strip()

        url = request.form.get(
            "url",
            ""
        ).strip()

        image = request.form.get(
            "image",
            ""
        )

        target_price = float(
            request.form.get("target_price") or price
        )

        # ==================================================
        # VALIDATION
        # ==================================================
        if not name or not url or price <= 0:

            flash(
                "Invalid product data.",
                "danger"
            )

            return redirect(url_for("web.dashboard"))

        # ==================================================
        # PREVENT DUPLICATE TRACKING
        # ==================================================
        existing = TrackedProduct.query.filter_by(
            user_id=current_user.id,
            product_url=url
        ).first()

        if existing:

            existing.is_active = True
            existing.target_price = target_price
            existing.alert_sent = False
            existing.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            flash(
                "Product tracking activated.",
                "success"
            )

            return redirect(
                url_for(
                    "web.product_detail",
                    product_id=existing.product_id
                )
            )

        # ==================================================
        # CREATE PRODUCT
        # ==================================================
        product = Product(
            title=name,
            price=price,
            old_price=None,
            image=image,
            website=website,
            source=website,
            url=url,
            user_id=current_user.id
        )

        db.session.add(product)
        db.session.flush()

        # ==================================================
        # CREATE PRODUCT LINK
        # ==================================================
        link = ProductLink(
            product_id=product.id,
            website=website,
            url=url,
            current_price=price
        )

        db.session.add(link)
        db.session.flush()

        # ==================================================
        # SAVE INITIAL PRICE HISTORY
        # ==================================================
        history = PriceHistory(
            link_id=link.id,
            product_id=product.id,
            old_price=None,
            price=price,
            price_change=0,
            change_percent=0,
            website=website,
            checked_at=datetime.now(timezone.utc)
        )

        db.session.add(history)

        # ==================================================
        # CREATE TRACKED PRODUCT
        # ==================================================
        tracked = TrackedProduct(
            user_id=current_user.id,
            product_id=product.id,
            product_name=name,
            website=website,
            price=price,
            old_price=None,
            target_price=target_price,
            product_url=url,
            is_active=True,
            alert_sent=False,
            last_checked=datetime.now(timezone.utc)
        )

        db.session.add(tracked)

        db.session.commit()

        log_activity(
            f"Started tracking: {name}"
        )

        flash(
            "Tracking started successfully!",
            "success"
        )

        return redirect(
            url_for(
                "web.product_detail",
                product_id=product.id
            )
        )

    except Exception as e:

        db.session.rollback()

        print("TRACK PRODUCT ERROR:", e)

        flash(
            "Tracking failed.",
            "danger"
        )

        return redirect(url_for("web.dashboard"))


# ==================================================
# PRODUCT DETAILS PAGE
# ==================================================
@web.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):

    # ==================================================
    # GET PRODUCT
    # ==================================================
    product = Product.query.get_or_404(product_id)

    # ==================================================
    # GET TRACKED INFO
    # ==================================================
    tracked = TrackedProduct.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    # ==================================================
    # GET PRODUCT LINKS
    # ==================================================
    links = ProductLink.query.filter_by(
        product_id=product.id
    ).all()

    if not links:

        flash(
            "No tracking links found for this product.",
            "warning"
        )

        return redirect(url_for("web.history"))

    # ==================================================
    # TRACKING DATA
    # ==================================================
    target_price = (
        tracked.target_price
        if tracked else None
    )

    is_active = (
        tracked.is_active
        if tracked else False
    )

    product_url = (
        tracked.product_url
        if tracked else product.url
    )

    # ==================================================
    # PRICE HISTORY
    # ==================================================
    history_data = []
    all_prices = []

    for link in links:

        histories = (
            PriceHistory.query
            .filter_by(link_id=link.id)
            .order_by(
                PriceHistory.checked_at.asc()
            )
            .all()
        )

        for h in histories:

            price = float(h.price or 0)

            history_data.append({
                "date": h.checked_at.strftime("%d %b %Y"),
                "timestamp": h.checked_at,
                "price": price,
                "website": link.website
            })

            all_prices.append(price)

    # ==================================================
    # SORT HISTORY
    # ==================================================
    history_data.sort(
        key=lambda x: x["timestamp"]
    )

    # ==================================================
    # PRICE ANALYTICS
    # ==================================================
    if not history_data:

        current_price = (
            float(
                tracked.price
                if tracked else product.price or 0
            )
        )

        highest_price = current_price
        lowest_price = current_price
        avg_price = current_price

        price_drop_percent = 0

        trend = "no-data"

    else:

        current_price = history_data[-1]["price"]

        highest_price = max(all_prices)

        lowest_price = min(all_prices)

        avg_price = round(
            sum(all_prices) / len(all_prices),
            2
        )

        price_drop_percent = round(
            (
                (highest_price - current_price)
                / highest_price
            ) * 100,
            2
        ) if highest_price > 0 else 0

        first_price = history_data[0]["price"]

        if len(history_data) < 2:

            trend = "stable"

        elif current_price < first_price:

            trend = "down"

        elif current_price > first_price:

            trend = "up"

        else:

            trend = "stable"

    # ==================================================
    # SMART INSIGHT
    # ==================================================
    smart_insight = "No target price set"

    if target_price:

        if current_price <= target_price:

            smart_insight = (
                "Below target price"
            )

        else:

            smart_insight = (
                "Still above target price"
            )

    # ==================================================
    # AI INSIGHTS
    # ==================================================
    ai_insights = []

    if price_drop_percent >= 10:

        ai_insights.append(
            "Big price drop detected!"
        )

    if (
        lowest_price
        and current_price == lowest_price
        and len(history_data) > 1
    ):

        ai_insights.append(
            "Lowest price ever recorded!"
        )

    if (
        target_price
        and current_price <= target_price
    ):

        ai_insights.append(
            "Target price reached!"
        )

    if trend == "down":

        ai_insights.append(
            "Price is trending downward"
        )

    elif trend == "up":

        ai_insights.append(
            "Price is increasing"
        )

    elif trend == "no-data":

        ai_insights.append(
            "Not enough data to analyze trend"
        )

    # ==================================================
    # GRAPH DATA
    # ==================================================
    graph_labels = [
        item["date"]
        for item in history_data
    ]

    graph_prices = [
        item["price"]
        for item in history_data
    ]

    # ==================================================
    # ACTIVITY LOG
    # ==================================================
    log_activity(
        f"Viewed product details: {product.title}"
    )

    # ==================================================
    # RENDER PAGE
    # ==================================================
    return render_template(
        "user/product_detail.html",

        product=product,
        tracked=tracked,
        product_url=product_url,

        current_price=current_price,
        highest_price=highest_price,
        lowest_price=lowest_price,
        avg_price=avg_price,

        target_price=target_price,

        smart_insight=smart_insight,

        ai_insights=ai_insights,
        alerts=ai_insights,

        price_drop_percent=price_drop_percent,
        trend=trend,

        is_active=is_active,

        graph_labels=graph_labels,
        graph_prices=graph_prices
    )


# ==================================================
# TOGGLE TRACKING
# ==================================================
@web.route(
    "/toggle-tracking/<int:tracked_id>",
    methods=["POST"]
)
@login_required
def toggle_tracking(tracked_id):

    item = TrackedProduct.query.get_or_404(
        tracked_id
    )

    # ==================================================
    # SECURITY CHECK
    # ==================================================
    if item.user_id != current_user.id:

        flash(
            "Unauthorized action.",
            "danger"
        )

        return redirect(url_for("web.dashboard"))

    # ==================================================
    # TOGGLE STATUS
    # ==================================================
    item.is_active = not item.is_active

    item.updated_at = datetime.now(
        timezone.utc
    )

    if item.is_active:
        item.alert_sent = False

    db.session.commit()

    # ==================================================
    # FLASH MESSAGE
    # ==================================================
    if item.is_active:

        flash(
            "Tracking activated.",
            "success"
        )

    else:

        flash(
            "Tracking stopped.",
            "warning"
        )

    return redirect(
        url_for(
            "web.product_detail",
            product_id=item.product_id
        )
    )


# ==================================================
# LOGOUT
# ==================================================
@web.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("web.home"))
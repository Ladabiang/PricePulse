from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

# ==================================================
# IMPORT MODELS / DB
# ==================================================
from app.extensions import db
from app.models.product import Product
from app.models.product_link import ProductLink
from app.models.price_history import PriceHistory
from app.models.tracked_product import TrackedProduct


# ==================================================
# BLUEPRINT
# ==================================================
user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


# ==================================================
# DASHBOARD
# ==================================================
@user_bp.route("/dashboard")
@login_required
def dashboard():

    tracked = TrackedProduct.query.filter_by(
        user_id=current_user.id
    ).all()

    active_alerts = sum(1 for item in tracked if item.is_active)

    return render_template(
        "user/dashboard.html",
        tracked_count=len(tracked),
        active_alerts=active_alerts,
        saved_items=len(tracked),
        searches=0,
        recent_tracking=tracked[:5]
    )


# ==================================================
# PRODUCTS PAGE
# SEARCH + PAGINATION
# ==================================================
@user_bp.route("/products")
@login_required
def products():

    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()

    query = Product.query

    if search:
        query = query.filter(
            or_(
                Product.title.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(
        Product.id.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template(
        "user/products.html",
        products=pagination.items,
        pagination=pagination,
        search=search
    )


# ==================================================
# PRODUCT DETAILS
# ==================================================
@user_bp.route("/product/<int:product_id>")
@login_required
def product_details(product_id):

    product = Product.query.get_or_404(product_id)

    links = ProductLink.query.filter_by(
        product_id=product.id
    ).all()

    # flexible history query
    history = PriceHistory.query.join(
        ProductLink,
        PriceHistory.link_id == ProductLink.id
    ).filter(
        ProductLink.product_id == product.id
    ).order_by(
        PriceHistory.checked_at.desc()
    ).limit(20).all()

    return render_template(
        "user/product_details.html",
        product=product,
        links=links,
        history=history
    )


# ==================================================
# ADD TO WATCHLIST
# ==================================================
@user_bp.route("/track/<int:product_id>", methods=["POST"])
@login_required
def track_product(product_id):

    product = Product.query.get_or_404(product_id)

    existing = TrackedProduct.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    if existing:
        flash("Already in watchlist.", "warning")
        return redirect(url_for("user.products"))

    tracked = TrackedProduct(
        user_id=current_user.id,
        product_id=product.id,
        product_name=product.title,
        website="Multiple Stores",
        price=0,
        target_price=0,
        is_active=True
    )

    db.session.add(tracked)
    db.session.commit()

    flash("Added to watchlist successfully.", "success")
    return redirect(url_for("user.watchlist"))


# ==================================================
# WATCHLIST
# ==================================================
@user_bp.route("/watchlist")
@login_required
def watchlist():

    page = request.args.get("page", 1, type=int)

    pagination = TrackedProduct.query.filter_by(
        user_id=current_user.id
    ).order_by(
        TrackedProduct.id.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template(
        "user/watchlist.html",
        items=pagination.items,
        pagination=pagination
    )


# ==================================================
# REMOVE WATCHLIST
# ==================================================
@user_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_watchlist(item_id):

    item = TrackedProduct.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("user.watchlist"))

    db.session.delete(item)
    db.session.commit()

    flash("Removed from watchlist.", "success")
    return redirect(url_for("user.watchlist"))


# ==================================================
# ALERTS
# ==================================================
@user_bp.route("/alerts")
@login_required
def alerts():

    page = request.args.get("page", 1, type=int)

    pagination = TrackedProduct.query.filter_by(
        user_id=current_user.id
    ).order_by(
        TrackedProduct.id.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template(
        "user/alerts.html",
        alerts=pagination.items,
        pagination=pagination
    )


# ==================================================
# TOGGLE ALERT
# ==================================================
@user_bp.route("/toggle-alert/<int:item_id>")
@login_required
def toggle_alert(item_id):

    item = TrackedProduct.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("user.alerts"))

    item.is_active = not item.is_active
    db.session.commit()

    flash("Alert status updated.", "success")
    return redirect(url_for("user.alerts"))


# ==================================================
# SEARCH PAGE
# ==================================================
@user_bp.route("/search")
@login_required
def search():

    keyword = request.args.get("q", "").strip()

    results = []

    if keyword:
        results = Product.query.filter(
            or_(
                Product.title.ilike(f"%{keyword}%"),
                Product.category.ilike(f"%{keyword}%")
            )
        ).all()

    return render_template(
        "user/search.html",
        products=results,
        query=keyword
    )


# ==================================================
# PROFILE
# ==================================================
@user_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "user/profile.html",
        user=current_user
    )


# ==================================================
# SETTINGS
# ==================================================
@user_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")

        if not username or not email:
            flash("Fields cannot be empty.", "error")
            return redirect(url_for("user.settings"))

        current_user.username = username
        current_user.email = email

        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.settings"))

    return render_template(
        "user/settings.html",
        user=current_user
    )
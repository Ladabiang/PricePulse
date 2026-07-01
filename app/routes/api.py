from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db

from app.models.product import Product
from app.models.product_link import ProductLink
from app.models.price_history import PriceHistory
from app.models.tracked_product import TrackedProduct
from datetime import datetime
from ..scrapers.base_scraper import search_all_sites
from ai_engine import predict_price

api_bp = Blueprint("api", __name__, url_prefix="/api")


# =========================================
# 1. ADD PRODUCT
# =========================================
@api_bp.route("/products", methods=["POST"])
@login_required
def add_product():

    data = request.get_json()

    name = data.get("name")
    price = data.get("price")
    website = data.get("website")
    url = data.get("url")

    if not name or not price:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        product = Product(
            title=name,
            user_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()

        link = ProductLink(
            product_id=product.id,
            website=website,
            url=url,
            current_price=price
        )
        db.session.add(link)
        db.session.commit()

        history = PriceHistory(
            link_id=link.id,
            price=price,
            checked_at=datetime.utcnow()
        )
        db.session.add(history)

        tracked = TrackedProduct(
            user_id=current_user.id,
            product_id=product.id,
            product_name=name,
            website=website,
            price=price,
            target_price=price,
            product_url=url
        )
        db.session.add(tracked)

        db.session.commit()

        return jsonify({
            "message": "Product added successfully",
            "product_id": product.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================
# 2. GET ALL PRODUCTS
# =========================================
@api_bp.route("/products", methods=["GET"])
@login_required
def get_products():

    products = Product.query.filter_by(user_id=current_user.id).all()

    data = []

    for p in products:
        data.append({
            "id": p.id,
            "title": p.title,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(data)


# =========================================
# 3. GET PRODUCT DETAILS
# =========================================
@api_bp.route("/products/<int:product_id>", methods=["GET"])
@login_required
def get_product(product_id):

    product = Product.query.get_or_404(product_id)

    links = ProductLink.query.filter_by(product_id=product.id).all()

    price_data = []

    for link in links:
        latest = PriceHistory.query.filter_by(link_id=link.id)\
            .order_by(PriceHistory.checked_at.desc()).first()

        if latest:
            price_data.append({
                "website": link.website,
                "price": latest.price,
                "url": link.url
            })

    return jsonify({
        "id": product.id,
        "title": product.title,
        "prices": price_data
    })


# =========================================
# 4. GET PRICE HISTORY
# =========================================
@api_bp.route("/history/<int:product_id>", methods=["GET"])
@login_required
def price_history(product_id):

    product = Product.query.get_or_404(product_id)

    links = ProductLink.query.filter_by(product_id=product.id).all()

    history_data = []
    price_list = []

    for link in links:
        history = PriceHistory.query.filter_by(link_id=link.id).all()

        for h in history:
            history_data.append({
                "price": h.price,
                "date": h.checked_at.strftime("%Y-%m-%d %H:%M")
            })
            price_list.append(h.price)

    #  AI Prediction Added
    prediction = predict_price(price_list) if price_list else {}

    return jsonify({
        "history": history_data,
        "prediction": prediction
    })


# =========================================
# 5. DELETE PRODUCT (REQUIRED)
# =========================================
@api_bp.route("/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": "Product deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================
# 6. TRIGGER SCRAPE MANUALLY (REQUIRED)
# =========================================
@api_bp.route("/scrape/<int:product_id>", methods=["POST"])
@login_required
def trigger_scrape(product_id):

    product = Product.query.get_or_404(product_id)

    try:
        results = search_all_sites(product.title)

        return jsonify({
            "message": f"Scraping completed for {product.title}",
            "results": results[:5]   # limit output
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# =========================================
# 7. SEARCH
# =========================================
@api_bp.route("/search", methods=["GET"])
def search_products():
    query = request.args.get("q", "").strip()

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    website = request.args.get("website", "").strip().lower()
    rating = request.args.get("rating", type=float)

    if not query:
        return jsonify({"error": "Search query required"}), 400

    try:
        results = search_all_sites(query) or []

        filtered = []

        for p in results:

            # ---------------- CLEAN PRICE ----------------
            price_raw = p.get("price", 0)

            try:
                # handles "₹1,299", "1299", None
                price = int(str(price_raw).replace("₹", "").replace(",", "").strip())
            except:
                price = 0

            # ---------------- CLEAN WEBSITE ----------------
            site = (p.get("website") or p.get("site") or "").strip().lower()

            # ---------------- CLEAN RATING ----------------
            try:
                rate = float(str(p.get("rating", 0)).strip())
            except:
                rate = 0.0

            # ---------------- FILTERS ----------------
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

            if website and website != "all" and website != site:
                continue

            if rating is not None and rate < rating:
                continue

            # ---------------- CLEAN TITLE ----------------
            title = p.get("title", "").strip()

            filtered.append({
                "title": title,
                "price": price,
                "image": p.get("image", ""),
                "url": p.get("url", ""),
                "website": site,
                "rating": rate,
                "reviews": p.get("reviews", 0),
                "price_drop_detected": p.get("price_drop_detected", False)
            })

        # Amazon-style sorting (lowest price first)
        filtered.sort(key=lambda x: x["price"])

        return jsonify({
            "query": query,
            "count": len(filtered),
            "results": filtered
        })

    except Exception as e:
        return jsonify({
            "error": "Search failed",
            "details": str(e)
        }), 500
# =========================================
# 8. UPDATE TARGET PRICE
# =========================================
@api_bp.route("/products/<int:product_id>/target", methods=["PUT"])
@login_required
def update_target(product_id):

    data = request.get_json()
    new_target = data.get("target_price")

    tracked = TrackedProduct.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()

    if not tracked:
        return jsonify({"error": "Tracked product not found"}), 404

    tracked.target_price = new_target
    db.session.commit()

    return jsonify({"message": "Target price updated"})
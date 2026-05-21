from flask import Blueprint, render_template, request
from app.models.product import Product
from sqlalchemy import and_

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():

    # =========================
    # GET FILTER VALUES
    # =========================
    category = request.args.get("category")
    source = request.args.get("source")
    price_min = request.args.get("price_min", type=float)
    price_max = request.args.get("price_max", type=float)
    sort = request.args.get("sort")
    drop_filter = request.args.get("drop_filter")

    # =========================
    # BASE QUERY
    # =========================
    query = Product.query

    # =========================
    # BASIC FILTERS
    # =========================
    if category:
        query = query.filter(Product.category == category)

    if source:
        query = query.filter(Product.source == source)

    if price_min is not None:
        query = query.filter(Product.price >= price_min)

    if price_max is not None:
        query = query.filter(Product.price <= price_max)

    # =========================
    # PRICE DROP SAFE LOGIC
    # =========================
    safe_drop_expr = None

    if drop_filter:

        # prevent NULL + division by zero
        safe_drop_expr = and_(
            Product.old_price.isnot(None),
            Product.old_price > 0,
            Product.price.isnot(None)
        )

        query = query.filter(safe_drop_expr)

        if drop_filter == "drop_only":
            query = query.filter(Product.old_price > Product.price)

        elif drop_filter == "drop_5":
            query = query.filter(
                (Product.old_price - Product.price) / Product.old_price >= 0.05
            )

        elif drop_filter == "drop_10":
            query = query.filter(
                (Product.old_price - Product.price) / Product.old_price >= 0.10
            )

    # =========================
    # SORTING
    # =========================
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())

    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())

    elif sort == "rating":
        query = query.order_by(Product.rating.desc())

    elif sort == "updated":
        query = query.order_by(Product.updated_at.desc())

    elif sort == "drop":
        query = query.order_by(
            (Product.old_price - Product.price).desc()
        )

    else:
        # default sort (important for UX)
        query = query.order_by(Product.updated_at.desc())

    # =========================
    # FETCH DATA
    # =========================
    products = query.limit(50).all()

    # =========================
    # STATS (OPTIMIZED + SAFE)
    # =========================
    total_products = Product.query.count()

    price_drops = Product.query.filter(
        Product.old_price.isnot(None),
        Product.price.isnot(None),
        Product.old_price > Product.price
    ).count()

    # TODO: replace this later with real alerts table
    active_alerts = 87

    # =========================
    # RENDER
    # =========================
    return render_template(
        "dashboard.html",
        products=products,
        total_products=total_products,
        price_drops=price_drops,
        active_alerts=active_alerts
    )
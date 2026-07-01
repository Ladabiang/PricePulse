from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import and_
import random

from app.models.product import Product
from app.scrapers.base_scraper import search_all_sites


dashboard_bp = Blueprint("dashboard", __name__)


# ==================================================
# TRENDING SEARCH QUERIES
# ==================================================
TRENDING_QUERIES = [
    #"iphone 16",
    #"samsung galaxy s25",
    #"oneplus 13",
    #"gaming smartphone",
    #"gaming laptop",
    #"macbook air",
    #"ultrabook laptop",
    #"boat rockerz",
    "wireless earbuds",
    #"marshall speaker",
    #"sony headphones",
    "nike sneakers",
    #"men oversized jacket",
    "women handbag",
    "playstation 5",
    #"gaming mouse",
    #"gaming keyboard",
    #"air fryer",
    "coffee machine",
    #"smart blender",
    #"smart watch",
    #"fitness band",
]


# ==================================================
# DASHBOARD
# ==================================================
@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    category = request.args.get("category")
    source = request.args.get("source")
    price_min = request.args.get("price_min", type=float)
    price_max = request.args.get("price_max", type=float)
    sort = request.args.get("sort")
    drop_filter = request.args.get("drop_filter")

    # ==================================================
    # TRENDING PRODUCTS FROM LIVE SCRAPER
    # ==================================================
    products = []

    selected_queries = random.sample(
        TRENDING_QUERIES,
        6
    )

    for q in selected_queries:

        try:
            items = search_all_sites(q) or []

            for item in items[:2]:

                if not isinstance(item, dict):
                    continue

                title = item.get("title") or item.get("product_name") or ""
                price = float(item.get("price") or 0)
                image = item.get("image") or "https://via.placeholder.com/300?text=No+Image"
                url = item.get("url") or item.get("product_url") or ""
                website = item.get("website") or item.get("site") or "Unknown"
                raw_rating = str(
                    item.get("rating") or "0"
                )

                try:
                    rating_value = float(
                        re.findall(
                            r"\d+\.?\d*",
                            raw_rating
                        )[0]
                    )
                except:
                    rating_value = 0
                reviews = item.get("reviews") or 0

                if not title or price <= 0 or not url:
                    continue

                products.append({
                    "product_name": title,
                    "title": title,
                    "price": price,
                    "old_price": price,
                    "image": image,
                    "product_url": url,
                    "url": url,
                    "website": website,
                    "rating": rating,
                    "reviews": reviews,
                    "price_drop_detected": False,
                    "drop_percent": 0,
                })

        except Exception as e:
            print("TRENDING PRODUCT ERROR:", e)
            continue

    random.shuffle(products)
    products = products[:12]

    # ==================================================
    # FALLBACK: DATABASE PRODUCTS IF SCRAPER RETURNS EMPTY
    # ==================================================
    if not products:

        query = Product.query

        if category:
            query = query.filter(Product.category == category)

        if source:
            query = query.filter(Product.source == source)

        if price_min is not None:
            query = query.filter(Product.price >= price_min)

        if price_max is not None:
            query = query.filter(Product.price <= price_max)

        if drop_filter:

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
            query = query.order_by(Product.updated_at.desc())

        db_products = query.limit(12).all()

        for p in db_products:

            products.append({
                "product_name": p.title,
                "title": p.title,
                "price": p.price,
                "old_price": p.old_price or p.price,
                "image": p.image,
                "product_url": p.url,
                "url": p.url,
                "website": p.source or "Unknown",
                "rating": getattr(p, "rating", 0) or 0,
                "reviews": getattr(p, "reviews", 0) or 0,
                "price_drop_detected": (
                    p.old_price and p.price and p.old_price > p.price
                ),
                "drop_percent": 0,
            })

    # ==================================================
    # STATS
    # ==================================================
    total_products = Product.query.count()

    price_drops = Product.query.filter(
        Product.old_price.isnot(None),
        Product.price.isnot(None),
        Product.old_price > Product.price
    ).count()

    active_alerts = 0

    # ==================================================
    # RENDER
    # ==================================================
    return render_template(
        "dashboard.html",
        products=products,
        total_products=total_products,
        price_drops=price_drops,
        active_alerts=active_alerts,
        tracked=total_products,
        alerts=active_alerts,
        drops=price_drops,
        savings=0,
        deal_filter="all"
    )
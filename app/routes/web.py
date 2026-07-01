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

import random

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
from app.scrapers.amazon import search_amazon

# ==================================================
# LOGGER
# ==================================================
from app.utils.log_activity import log_activity
from app.services.price_predictor import predict_next_price

# ==================================================
# BLUEPRINT
# ==================================================
web = Blueprint("web", __name__)

FILTER_QUERIES = {
    # ================= ELECTRONICS =================
    "smartphones": {
        "query": "smartphone mobile phone 5g",
        "keywords": ["smartphone", "mobile", "phone", "galaxy", "iphone", "redmi", "realme", "oneplus", "5g"],
        "exclude": ["case", "cover", "back cover", "flip cover","tempered", "tempered glass", "screen guard","screen protector", "protector", "camera protector","lens protector", "skin", "sticker", "decal",
        "charger", "fast charger", "adapter",
        "cable", "usb cable", "type c cable",
        "lightning cable", "otg", "power adapter",
        "holder", "stand", "tripod",
        "ring holder", "mount",
        "wallet case", "bumper",
        "battery replacement", "spare battery",
        "sim tray", "replacement screen",
        "mobile pouch", "phone bag",
        "phone grip", "popsocket",
        "repair kit", "tool kit"]
    },

    "gamingphones": {
        "query": "gaming phone mobile",
        "keywords": ["gaming", "phone", "mobile", "smartphone", "5g"],
        "exclude": ["case", "cover", "back cover", "flip cover",
        "tempered", "tempered glass", "screen guard",
        "screen protector", "protector", "camera protector",
        "lens protector", "skin", "sticker", "decal",
        "charger", "fast charger", "adapter",
        "cable", "usb cable", "type c cable",
        "lightning cable", "otg", "power adapter",
        "holder", "stand", "tripod",
        "ring holder", "mount",
        "wallet case", "bumper",
        "battery replacement", "spare battery",
        "sim tray", "replacement screen",
        "mobile pouch", "phone bag",
        "phone grip", "popsocket",
        "repair kit", "tool kit"]
    },

    "budgetphones": {
        "query": "budget smartphone mobile phone",
        "keywords": ["smartphone", "mobile", "phone", "5g", "android"],
        "exclude": ["case", "cover", "back cover", "flip cover","tempered", "tempered glass", "screen guard","screen protector", "protector", "camera protector","lens protector", "skin", "sticker", "decal",
        "charger", "fast charger", "adapter",
        "cable", "usb cable", "type c cable",
        "lightning cable", "otg", "power adapter",
        "holder", "stand", "tripod",
        "ring holder", "mount",
        "wallet case", "bumper",
        "battery replacement", "spare battery",
        "sim tray", "replacement screen",
        "mobile pouch", "phone bag",
        "phone grip", "popsocket",
        "repair kit", "tool kit"]
    },

    "tablets": {
        "query": "tablet ipad tab",
        "keywords": ["tablet", "ipad", "tab"],
        "exclude": ["case", "cover", "back cover", "flip cover","tempered", "tempered glass", "screen guard","screen protector", "protector", "camera protector","lens protector", "skin", "sticker", "decal",
        "charger", "fast charger", "adapter",
        "cable", "usb cable", "type c cable",
        "lightning cable", "otg", "power adapter",
        "holder", "stand", "tripod",
        "ring holder", "mount",
        "wallet case", "bumper",
        "battery replacement", "spare battery",
        "sim tray", "replacement screen",
        "mobile pouch", "phone bag",
        "phone grip", "popsocket",
        "repair kit", "tool kit"]
    },

   "smartwatches": {
        "query": "smartwatch smart watch",
        "keywords": ["smartwatch", "smart watch", "watch", "colorfit", "fire-boltt", "noise"],
        "exclude": [
            "strap", "band", "replacement band", "silicone strap", "metal strap",
            "charger", "charging cable", "dock", "case", "cover", "screen guard",
            "protector", "tempered", "glass", "stand", "holder", "watch box",
            "watch pouch", "repair kit"
        ]
    },

    "chargers": {
        "query": "mobile charger fast charger",
        "keywords": ["charger", "adapter", "fast charger"],
        "exclude": [
            "phone", "mobile", "smartphone", "case", "cover", "screen guard",
            "tempered", "glass", "protector", "holder", "stand", "pouch"
        ]
    },

    "powerbanks": {
        "query": "power bank powerbank",
        "keywords": ["power bank", "powerbank", "mah"],
        "exclude": [
            "case", "cover", "pouch", "charger only", "adapter only", "usb cable",
            "type c cable", "charging cable", "stand", "holder", "spare cell",
            "battery replacement"
        ]
    },

    "cables": {
        "query": "usb charging cable type c cable",
        "keywords": ["cable", "usb", "type c", "lightning"],
        "exclude": [
            "charger", "adapter", "phone", "mobile", "case", "cover",
            "screen guard", "protector", "holder", "stand"
        ]
    },

    "cases": {
        "query": "mobile phone case cover",
        "keywords": ["case", "cover", "back cover"],
        "exclude": [
            "phone", "mobile phone", "smartphone", "charger", "adapter",
            "cable", "tempered glass", "screen guard"
        ]
    },

    # ================= COMPUTING =================
    "laptops": {
        "query": "laptop computer",
        "keywords": ["laptop", "notebook", "vivobook", "ideapad", "thinkpad", "victus"],
        "exclude": [
            "bag", "laptop bag", "sleeve", "case", "cover", "charger", "adapter",
            "keyboard", "keyboard cover", "mouse", "mouse pad", "cooling pad",
            "stand", "dock", "hub", "screen guard", "protector", "skin", "sticker",
            "ram", "ssd", "hard disk", "webcam", "microphone", "battery replacement"
        ]
    },

    "gaming-laptops": {
        "query": "gaming laptop",
        "keywords": ["gaming laptop", "laptop", "rtx", "gtx", "gaming"],
        "exclude": [
            "bag", "sleeve", "case", "cover", "charger", "adapter", "keyboard",
            "mouse", "cooling pad", "stand", "skin", "sticker", "ram", "ssd"
        ]
    },

    "ultrabooks": {
        "query": "ultrabook thin laptop",
        "keywords": ["ultrabook", "laptop", "thin", "lightweight"],
        "exclude": [
            "bag", "sleeve", "case", "cover", "charger", "adapter",
            "keyboard", "mouse", "stand", "skin", "sticker"
        ]
    },

    "macbooks": {
        "query": "apple macbook laptop",
        "keywords": ["macbook", "apple", "m1", "m2", "m3", "m4"],
        "exclude": [
            "case", "cover", "sleeve", "charger", "adapter", "keyboard cover",
            "screen guard", "protector", "stand", "skin", "sticker", "hub", "dock"
        ]
    },

    "desktops": {
        "query": "desktop pc computer",
        "keywords": ["desktop", "pc", "computer", "cpu"],
        "exclude": [
            "monitor", "keyboard", "mouse", "cable", "adapter", "stand",
            "speaker", "webcam", "ups", "cabinet only"
        ]
    },

    "monitors": {
        "query": "computer monitor",
        "keywords": ["monitor", "display"],
        "exclude": [
            "stand", "mount", "wall mount", "hdmi cable", "vga cable",
            "display cable", "adapter", "screen protector", "cover", "cleaning kit",
            "replacement panel"
        ]
    },

    "printers": {
        "query": "printer inkjet laser printer",
        "keywords": ["printer", "inkjet", "laser"],
        "exclude": [
            "ink", "cartridge", "toner", "paper", "cable", "cover",
            "printer stand", "refill", "cleaning kit"
        ]
    },

    # ================= ENTERTAINMENT =================
    "smart-tv": {
        "query": "smart tv television",
        "keywords": ["smart tv", "television", "led tv", "android tv", "google tv"],
        "exclude": [
            "remote", "remote cover", "stand", "wall mount", "tv unit", "sticker",
            "screen guard", "screen protector", "hdmi cable", "adapter", "cleaning kit",
            "replacement remote"
        ]
    },

    "oled-tv": {
        "query": "led tv oled tv television",
        "keywords": ["oled", "led tv", "television", "tv"],
        "exclude": [
            "remote", "remote cover", "stand", "wall mount", "tv unit",
            "screen guard", "hdmi cable", "adapter", "cleaning kit"
        ]
    },

    "streaming": {
        "query": "streaming device fire tv stick chromecast",
        "keywords": ["fire tv", "chromecast", "streaming", "tv stick"],
        "exclude": [
            "remote cover", "case", "cover", "cable", "adapter", "holder", "stand"
        ]
    },

    "soundbars": {
        "query": "soundbar speaker",
        "keywords": ["soundbar", "sound bar"],
        "exclude": [
            "cover", "stand", "wall mount", "cable", "remote", "adapter", "bracket"
        ]
    },

    "home-theatre": {
        "query": "home theatre speaker system",
        "keywords": ["home theatre", "home theater", "speaker system"],
        "exclude": [
            "stand", "cable", "remote", "cover", "adapter", "wall mount", "bracket"
        ]
    },

    "speakers": {
        "query": "speaker bluetooth speaker",
        "keywords": ["speaker", "bluetooth speaker"],
        "exclude": [
            "stand", "case", "cover", "cable", "charger", "adapter", "mount", "skin"
        ]
    },

    # ================= AUDIO =================
    "earbuds": {
        "query": "wireless earbuds tws",
        "keywords": ["earbuds", "earbud", "tws", "airdopes", "buds"],
        "exclude": [
            "case", "cover", "silicone case", "ear tips", "earbuds case",
            "hook", "clip", "charger", "charging cable", "skin", "sticker",
            "cleaning kit", "cleaning pen", "replacement battery"
        ]
    },

    "headphones": {
        "query": "bluetooth headphones",
        "keywords": ["headphone", "headphones", "rockerz"],
        "exclude": [
            "case", "cover", "ear cushions", "ear pads", "cable", "adapter",
            "stand", "holder", "hanger", "skin", "sticker", "replacement battery"
        ]
    },

    "neckbands": {
        "query": "bluetooth neckband earphones",
        "keywords": ["neckband", "earphone", "earphones"],
        "exclude": [
            "case", "cover", "cable", "charger", "ear tips", "hook", "clip",
            "skin", "cleaning kit"
        ]
    },

    "bluetooth-speakers": {
        "query": "bluetooth speaker",
        "keywords": ["bluetooth speaker", "speaker"],
        "exclude": [
            "case", "cover", "stand", "holder", "charger", "cable", "adapter",
            "mount", "skin", "replacement battery"
        ]
    },

    "wearables": {
        "query": "smart wearable fitness band",
        "keywords": ["wearable", "fitness band", "smart band", "smartwatch", "smart watch"],
        "exclude": [
            "strap", "band replacement", "replacement band", "charger", "case",
            "cover", "screen guard", "protector", "tempered glass", "dock"
        ]
    },

    # ================= MEN =================
    "tshirts": {
        "query": "men t shirt polo",
        "keywords": ["t-shirt", "tshirt", "tee", "polo"],
        "exclude": [
            "women", "kids", "girl", "boy", "hanger", "sticker", "patch",
            "badge", "brooch", "keychain", "bag", "cap", "belt", "sock",
            "shorts", "pants", "combo with shorts", "combo with pants"
        ]
    },

    "shirts": {
        "query": "men shirt",
        "keywords": ["shirt"],
        "exclude": [
            "women", "kids", "girl", "boy", "t-shirt", "tshirt",
            "hanger", "patch", "badge", "tie", "belt", "cap", "bag", "combo"
        ]
    },

    "jeans": {
        "query": "men jeans",
        "keywords": ["jeans", "denim"],
        "exclude": [
            "women", "kids", "girl", "boy", "jacket", "belt", "wallet",
            "keychain", "patch", "sticker", "combo", "bag", "cap"
        ]
    },

    "jackets": {
        "query": "men jacket",
        "keywords": ["jacket", "coat"],
        "exclude": [
            "women", "kids", "girl", "boy", "hanger", "patch", "badge"
        ]
    },

    "ethnic": {
        "query": "men ethnic wear kurta",
        "keywords": ["kurta", "ethnic", "sherwani"],
        "exclude": [
            "women", "kids", "saree", "lehenga", "dupatta", "blouse", "jewellery"
        ]
    },

    "innerwear": {
        "query": "men innerwear",
        "keywords": ["innerwear", "brief", "vest", "trunk"],
        "exclude": [
            "women", "kids", "bra", "panty", "camisole", "slip"
        ]
    },

    # ================= WOMEN =================
    "dresses": {
        "query": "women dress",
        "keywords": ["dress", "gown"],
        "exclude": [
            "men", "boys", "kids", "shirt", "t-shirt", "tshirt", "hanger",
            "belt only", "dupatta only", "blouse only"
        ]
    },

    "kurtis": {
        "query": "women kurti",
        "keywords": ["kurti", "kurta"],
        "exclude": [
            "men", "boys", "kids", "dupatta only", "pant only", "legging only",
            "hanger", "sticker"
        ]
    },

    "sarees": {
        "query": "women saree",
        "keywords": ["saree", "sari"],
        "exclude": [
            "men", "boys", "kids", "blouse only", "petticoat", "dupatta",
            "hanger", "fall pico", "saree cover"
        ]
    },

    "tops": {
        "query": "women tops tees",
        "keywords": ["top", "tops", "tee", "t-shirt"],
        "exclude": [
            "men", "boys", "kids", "hanger", "sticker", "patch", "badge"
        ]
    },

    # ================= FOOTWEAR =================
    "sneakers": {
        "query": "sneakers shoes",
        "keywords": ["sneaker", "sneakers", "shoes"],
        "exclude": [
            "lace", "laces", "shoe lace", "insole", "insoles", "shoe bag",
            "shoe rack", "shoe cleaner", "shoe polish", "deodorizer",
            "sock", "socks", "shoe tree", "shoe horn"
        ]
    },

    "running": {
        "query": "running shoes",
        "keywords": ["running shoe", "running shoes", "shoes"],
        "exclude": [
            "lace", "laces", "shoe lace", "insole", "insoles", "shoe bag",
            "shoe rack", "shoe cleaner", "shoe polish", "deodorizer",
            "sock", "socks", "shoe tree", "shoe horn"
        ]
    },

    "formal": {
        "query": "formal shoes",
        "keywords": ["formal shoe", "formal shoes", "shoes"],
        "exclude": [
            "lace", "laces", "shoe lace", "insole", "insoles", "shoe bag",
            "shoe rack", "shoe cleaner", "shoe polish", "sock", "socks",
            "shoe tree", "shoe horn"
        ]
    },

    "sandals": {
        "query": "sandals",
        "keywords": ["sandal", "sandals"],
        "exclude": [
            "shoe", "sneaker", "lace", "insole", "cleaner", "polish",
            "sock", "shoe rack"
        ]
    },

    "slippers": {
        "query": "slippers flip flops",
        "keywords": ["slipper", "slippers", "flip flop", "flip-flop"],
        "exclude": [
            "shoe", "sneaker", "lace", "insole", "cleaner", "polish",
            "sock", "shoe rack"
        ]
    },

    "sports": {
        "query": "sports shoes",
        "keywords": ["sports shoe", "sports shoes", "shoes"],
        "exclude": [
            "lace", "laces", "shoe lace", "insole", "insoles", "shoe bag",
            "shoe rack", "shoe cleaner", "shoe polish", "sock", "socks"
        ]
    },

    # ================= JEWELLERY =================
    "gold": {
        "query": "gold jewellery",
        "keywords": ["gold", "jewellery", "jewelry"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },
    "silver": {
        "query": "silver jewellery",
        "keywords": ["silver", "jewellery", "jewelry"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },
    "artificial": {
        "query": "artificial jewellery fashion jewellery",
        "keywords": ["artificial", "fashion jewellery", "jewellery", "jewelry"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },
    "rings": {
        "query": "rings jewellery",
        "keywords": ["ring", "rings"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },
    "necklaces": {
        "query": "necklace jewellery",
        "keywords": ["necklace", "necklaces", "chain"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },
    "earrings": {
        "query": "earrings jewellery",
        "keywords": ["earring", "earrings"],
        "exclude": ["box", "gift box", "stand", "display stand", "cleaner", "polish", "pouch", "storage box", "repair kit"]
    },

    # ================= BEAUTY =================
    "makeup": {
        "query": "makeup cosmetics",
        "keywords": ["makeup", "cosmetic", "lipstick", "foundation", "mascara", "eyeliner"],
        "exclude": ["bag", "box", "organizer", "brush holder", "mirror", "empty bottle", "applicator only", "pouch"]
    },
    "skincare": {
        "query": "skincare face cream serum",
        "keywords": ["skincare", "cream", "serum", "face wash", "moisturizer", "sunscreen"],
        "exclude": ["bag", "box", "organizer", "brush", "applicator", "empty bottle", "pouch"]
    },
    "haircare": {
        "query": "hair care shampoo conditioner",
        "keywords": ["hair", "shampoo", "conditioner", "hair oil", "serum"],
        "exclude": ["comb", "brush", "clip", "rubber band", "headband", "empty bottle", "applicator"]
    },
    "grooming": {
        "query": "grooming trimmer shaver",
        "keywords": ["grooming", "trimmer", "shaver", "razor"],
        "exclude": ["blade only", "comb", "oil", "brush", "charger", "charging cable", "stand", "case", "cover", "replacement head"]
    },
    "fragrance": {
        "query": "perfume fragrance deodorant",
        "keywords": ["perfume", "fragrance", "deodorant", "body spray"],
        "exclude": ["empty bottle", "holder", "box only", "gift box only", "pouch"]
    },

    # ================= HOME =================
    "appliances": {
        "query": "kitchen appliances",
        "keywords": ["appliance", "mixer", "grinder", "kettle", "toaster", "air fryer", "juicer"],
        "exclude": ["cover", "stand", "tray", "spare part", "blade only", "paper liner", "silicone liner", "basket", "rack", "tongs", "recipe book", "cleaning brush"]
    },
    "cookware": {
        "query": "cookware kitchen",
        "keywords": ["cookware", "pan", "kadai", "tawa", "pot"],
        "exclude": ["lid only", "handle", "stand", "cleaner", "scrubber", "spare part"]
    },
    "storage": {
        "query": "kitchen storage container",
        "keywords": ["storage", "container", "box", "jar"],
        "exclude": ["label", "sticker", "stand", "rack only", "lid only"]
    },
    "decor": {
        "query": "home decor",
        "keywords": ["decor", "decoration", "wall art", "showpiece", "painting"],
        "exclude": ["hook", "tape", "nail", "hanger only", "stand only", "frame only"]
    },
    "cleaning": {
        "query": "cleaning tools home",
        "keywords": ["cleaning", "mop", "broom", "brush", "wiper"],
        "exclude": ["refill only", "handle only", "bucket only", "spare part"]
    }
}


# ==================================================
# SMART CATEGORY FILTER
# ==================================================
def contains_any(text, words):
    text = str(text or "").lower()
    return any(word.lower() in text for word in words)


def filter_results_by_category(results, sub, min_price=None, max_price=None, marketplace=""):
    config = FILTER_QUERIES.get(sub)
    cleaned = []

    for item in results:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or item.get("product_name") or "").lower()
        website = str(item.get("website") or item.get("site") or "").lower()

        try:
            price = float(item.get("price") or 0)
        except:
            price = 0

        if not title or title == "n/a":
            continue

        if price <= 0:
            continue

        if min_price and price < min_price:
            continue

        if max_price and price > max_price:
            continue

        if marketplace and website != marketplace.lower():
            continue

        if config:
            keywords = config.get("keywords", [])
            exclude = config.get("exclude", [])

            if keywords and not contains_any(title, keywords):
                continue

            if exclude and contains_any(title, exclude):
                continue

        cleaned.append(item)

    results = filter_results_by_category(
        cleaned,
        sub,
        None,
        None,
        ""
    )

# ==========================================
# AUTO DETECT PRODUCT CATEGORY
# ==========================================
def detect_sub_from_query(query):

    q = str(query or "").lower()

    # Smartphones
    if any(x in q for x in [
        "iphone",
        "galaxy",
        "redmi",
        "realme",
        "oneplus",
        "smartphone",
        "mobile",
        "5g"
    ]):
        return "smartphones"

    # Laptops
    if any(x in q for x in [
        "laptop",
        "macbook",
        "victus",
        "vivobook",
        "ideapad",
        "notebook"
    ]):
        return "laptops"

    # Earbuds
    if any(x in q for x in [
        "earbuds",
        "airdopes",
        "buds",
        "tws"
    ]):
        return "earbuds"

    # Headphones
    if any(x in q for x in [
        "headphones",
        "headphone",
        "rockerz"
    ]):
        return "headphones"

    # Smartwatch
    if any(x in q for x in [
        "smartwatch",
        "smart watch",
        "fire-boltt",
        "noise",
        "colorfit"
    ]):
        return "smartwatches"

    # Power Bank
    if any(x in q for x in [
        "power bank",
        "powerbank",
        "mah"
    ]):
        return "powerbanks"

    # T-Shirts
    if any(x in q for x in [
        "t shirt",
        "t-shirt",
        "tshirt",
        "polo"
    ]):
        return "tshirts"

    # Shoes
    if any(x in q for x in [
        "running shoes",
        "sneakers",
        "sports shoes"
    ]):
        return "running"

    # Kitchen Appliances
    if any(x in q for x in [
        "air fryer",
        "kettle",
        "grinder",
        "mixer"
    ]):
        return "appliances"

    # Grooming
    if any(x in q for x in [
        "trimmer",
        "shaver",
        "razor"
    ]):
        return "grooming"

    return ""
# ==================================================
# HOME PAGE
# ==================================================
@web.route("/")
def home():

    return render_template("auth/index.html")


# ==================================================
# DASHBOARD
# ==================================================
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

    tracked = len(tracked_items)

    alerts = len([
        p for p in tracked_items
        if p.target_price and p.price <= p.target_price
    ])

    drops = 0
    savings = 0

    for p in tracked_items:

        histories = (
            PriceHistory.query
            .filter_by(product_id=p.product_id)
            .order_by(PriceHistory.checked_at.asc())
            .all()
        )

        for h in histories:

            old_price = float(h.old_price or 0)
            new_price = float(h.price or 0)

            if old_price > new_price:
                drops += 1
                savings += old_price - new_price

    savings = round(savings, 2)
    deal_filter = request.args.get("deal_filter", "all")

    # ==================================================
    # LIVE TRENDING PRODUCTS
    # ==================================================
    TRENDING_QUERIES = [
        "iphone 16",
        "samsung galaxy s25",
        "gaming laptop",
        "macbook air",
        "wireless earbuds",
        "boat rockerz",
        "nike sneakers",
        "playstation 5",
        "smart watch",
        "gaming mouse",
        "coffee machine",
        "air fryer"
    ]

    products = []

    try:
        selected_queries = random.sample(TRENDING_QUERIES, 4)

        for q in selected_queries:

            items = search_all_sites(q) or []
            for item in items[:2]:

                title = item.get("title") or ""
                price = float(item.get("price") or 0)
                image = item.get("image") or "https://via.placeholder.com/300?text=No+Image"
                url = item.get("url") or ""
                website = item.get("website") or item.get("site") or "Unknown"

                if not title or price <= 0 or not url:
                    continue

                products.append({
                    "product_name": title,
                    "price": price,
                    "old_price": price,
                    "image": image,
                    "product_url": url,
                    "website": website,
                    "price_drop_detected": False,
                    "drop_percent": 0
                })

        random.shuffle(products)
        products = products[:12]

    except Exception as e:
        print("TRENDING DASHBOARD ERROR:", e)
        products = tracked_items

    # ==================================================
    # DEAL FILTERS
    # ==================================================
    if deal_filter == "budget":
        products = [
            p for p in products
            if p["price"] and 10000 <= p["price"] <= 30000
        ]

    elif deal_filter == "laptops":
        products = [
            p for p in products
            if "laptop" in p["product_name"].lower()
            or "macbook" in p["product_name"].lower()
        ]

    elif deal_filter == "smartphones":
        products = [
            p for p in products
            if "phone" in p["product_name"].lower()
            or "mobile" in p["product_name"].lower()
            or "iphone" in p["product_name"].lower()
            or "5g" in p["product_name"].lower()
        ]

    return render_template(
        "user/dashboard.html",
        products=products,
        deal_filter=deal_filter,
        tracked=tracked,
        alerts=alerts,
        drops=drops,
        savings=savings
    )

# ==================================================
# HISTORY PAGE
# ==================================================
@web.route("/history")
@login_required
def history():

    products = (
        TrackedProduct.query
        .filter_by(
            user_id=current_user.id,
            is_active=True
        )
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
        TrackedProduct.query
        .filter(
            TrackedProduct.user_id == current_user.id,
            TrackedProduct.is_active == True,
            TrackedProduct.price <= TrackedProduct.target_price
        )
        .order_by(TrackedProduct.last_checked.desc())
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
        .filter_by(
            user_id=current_user.id,
            is_active=False
        )
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
@web.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    from app.extensions import db, bcrypt

    if request.method == "POST":

        form_type = request.form.get("form_type")

        # ==================================================
        # PROFILE SETTINGS
        # ==================================================
        if form_type == "profile":

            username = request.form.get("username")
            email = request.form.get("email")

            current_user.username = username
            current_user.email = email

            db.session.commit()

            flash(
                "Profile updated successfully!",
                "success"
            )

            return redirect(url_for("web.settings"))

        # ==================================================
        # NOTIFICATION SETTINGS
        # ==================================================
        elif form_type == "notifications":

            current_user.email_alerts = (
                request.form.get("email_alerts") == "on"
            )

            current_user.push_notifications = (
                request.form.get("push_notifications") == "on"
            )

            current_user.weekly_reports = (
                request.form.get("weekly_reports") == "on"
            )

            db.session.commit()

            flash(
                "Notification settings updated!",
                "success"
            )

            return redirect(url_for("web.settings"))

        # ==================================================
        # PASSWORD UPDATE
        # ==================================================
        elif form_type == "security":

            current_password = request.form.get(
                "current_password"
            )

            new_password = request.form.get(
                "new_password"
            )

            confirm_password = request.form.get(
                "confirm_password"
            )

            # ==============================================
            # VALIDATE CURRENT PASSWORD
            # ==============================================
            if not bcrypt.check_password_hash(
                current_user.password,
                current_password
            ):

                flash(
                    "Current password is incorrect",
                    "error"
                )

                return redirect(url_for("web.settings"))

            # ==============================================
            # CONFIRM PASSWORD MATCH
            # ==============================================
            if new_password != confirm_password:

                flash(
                    "Passwords do not match",
                    "error"
                )

                return redirect(url_for("web.settings"))

            # ==============================================
            # UPDATE PASSWORD
            # ==============================================
            hashed_password = bcrypt.generate_password_hash(
                new_password
            ).decode("utf-8")

            current_user.password = hashed_password

            db.session.commit()

            flash(
                "Password updated successfully!",
                "success"
            )

            return redirect(url_for("web.settings"))

    # ======================================================
    # GET REQUEST
    # ======================================================
    return render_template(
        "user/settings.html"
    )
# ==================================================
# SHOP PAGE
# ==================================================
@web.route("/shop")
@login_required
def shop():

    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sub = request.args.get("sub", "").strip()
    marketplace = request.args.get("marketplace", "").strip()
    brand = request.args.get("brand", "").strip()
    rating_filter = request.args.get("rating", "").strip()
    sort_by = request.args.get("sort_by", "").strip()
    discount = request.args.get("discount", "").strip()

    discount = request.args.get(
        "discount",
        ""
    ).strip()

    ai_filter = request.args.get(
        "ai_filter",
        ""
    ).strip()

    # ==============================
    # SAFE PRICE INPUTS
    # ==============================
    try:
        min_price = float(request.args.get("min") or 0)
    except:
        min_price = 0

    try:
        max_price = float(request.args.get("max") or 0)
    except:
        max_price = 0

    # ==============================
    # BUILD SEARCH QUERY
    # ==============================
    search_query = query

    if not search_query:

        if sub in FILTER_QUERIES:
            search_query = FILTER_QUERIES[sub].get("query", "")

        elif sub:
            search_query = sub.replace("-", " ")

        elif category:
            search_query = category.replace("-", " ")

    results = []
    available_brands = []

    # ==============================
    # RUN SCRAPER SAFELY
    # ==============================
    if search_query:

        try:
            raw_results = search_all_sites(search_query) or []

        except Exception as e:
            print("SHOP SCRAPER ERROR:", e)
            raw_results = []

        cleaned = []

        for item in raw_results:

            try:
                if not isinstance(item, dict):
                    continue

                title = (
                    item.get("title")
                    or item.get("product_name")
                    or ""
                ).strip()

                price = float(item.get("price") or 0)

                old_price = float(
                    item.get("old_price")
                    or price * 1.10
                )

                image = (
                    item.get("image")
                    or "https://via.placeholder.com/300?text=No+Image"
                )

                url = (
                    item.get("url")
                    or item.get("product_url")
                    or ""
                )

                website = (
                    item.get("website")
                    or item.get("site")
                    or "Unknown"
                )

                raw_rating = str(item.get("rating") or "0")

                try:
                    rating_value = float(
                        re.findall(r"\d+\.?\d*", raw_rating)[0]
                    )
                except:
                    rating_value = 0
                reviews = item.get("reviews") or 0

                # BRAND FILTER
                if brand:

                    if brand.lower() not in title.lower():
                        continue

                if not title or title == "N/A":
                    continue

                if price <= 0:
                    continue

                if not url:
                    continue

                # RATING FILTER
                if rating_filter:

                    try:

                        if float(item.get("rating") or 0) < float(rating_filter):
                            continue

                    except:
                        pass

                # ==============================
                # PRICE FILTERS
                # ==============================
                if min_price > 0 and price < min_price:
                    continue

                if max_price > 0 and price > max_price:
                    continue

                # ==============================
                # MARKETPLACE FILTER
                # ==============================
                if marketplace:
                    if website.lower() != marketplace.lower():
                        continue
                

                # ==========================
                # DISCOUNT FILTER
                # ==========================
                if discount:

                    try:

                        discount_percent = (
                            (old_price - price)
                            / old_price
                        ) * 100

                        if discount_percent < float(discount):
                            continue

                    except:
                        pass

                # ==========================
                # AI RECOMMENDATION
                # ==========================
                recommendation = "stable"

                if rating_value >= 4.3:
                    recommendation = "buy"

                elif rating_value < 3.5:
                    recommendation = "wait"
                cleaned.append({
                    "title": title,
                    "price": price,
                    "image": image,
                    "url": url,
                    "website": website,
                    "rating": rating_value,
                    "reviews": reviews,
                    "ai_recommendation":
                        recommendation
                })

            except Exception as e:
                print("SHOP ITEM CLEAN ERROR:", e)
                continue

        # ==========================================
        # DYNAMIC BRANDS
        # ==========================================
        

        COMMON_BRANDS = [

            "Samsung", "Apple", "OnePlus", "Realme", "Redmi",
            "Xiaomi", "POCO", "Vivo", "Oppo",

            "boAt", "Noise", "JBL", "Sony",
            "Boult", "Fire-Boltt",

            "HP", "Dell", "Lenovo", "Asus", "Acer",

            "Nike", "Puma", "Adidas",
            "Levis", "Allen Solly",
            "Biba", "Libas",

            "Prestige", "Philips",
            "Havells", "Bajaj"
        ]

        for item in cleaned:

            title = item.get("title", "").lower()

            for b in COMMON_BRANDS:

                if b.lower() in title:

                    if b not in available_brands:
                        available_brands.append(b)
        # ==============================
        # CATEGORY FILTER SAFELY
        # ==============================
        try:
            results = filter_results_by_category(
                cleaned,
                sub,
                min_price if min_price > 0 else None,
                max_price if max_price > 0 else None,
                marketplace
            )

            # ==========================
            # AI FILTER
            # ==========================
            if ai_filter:

                results = [

                    item

                    for item in results

                    if item.get(
                        "ai_recommendation",
                        "stable"
                    ) == ai_filter

                ]
            
            # SORTING
            if sort_by == "low_price":

                results.sort(
                    key=lambda x: float(x.get("price", 0))
                )

            elif sort_by == "high_price":

                results.sort(
                    key=lambda x: float(x.get("price", 0)),
                    reverse=True
                )

            elif sort_by == "rating":

                results.sort(
                    key=lambda x: float(x.get("rating", 0)),
                    reverse=True
                )

            amazon_count = len([
                x for x in results
                if x.get("website") == "Amazon"
            ])

            flipkart_count = len([
                x for x in results
                if x.get("website") == "Flipkart"
            ])

            snapdeal_count = len([
                x for x in results
                if x.get("website") == "Snapdeal"
            ])

            shopclues_count = len([
                x for x in results
                if x.get("website") == "ShopClues"
            ])

            print("\n===== SHOP RESULTS =====")
            print("Amazon:", amazon_count)
            print("Flipkart:", flipkart_count)
            print("Snapdeal:", snapdeal_count)
            print("ShopClues:", shopclues_count)
            print("Total:", len(results))
            print("========================\n")
        except Exception as e:
            print("CATEGORY FILTER ERROR:", e)
            results = cleaned

        try:
            log_activity(
                f"Filtered shop search: {search_query}"
            )
        except:
            pass

    return render_template(
        "user/search_product.html",
        results=results,
        query=search_query or "",
        category=category,
        sub=sub,
        min_price=min_price if min_price > 0 else "",
        max_price=max_price if max_price > 0 else "",
        marketplace=marketplace,
        brand=brand,
        available_brands=available_brands,
        rating=rating_filter,
        sort_by=sort_by,
        discount=discount,
        ai_filter=ai_filter
    )


# ==================================================
# HELPER: CLEAN PRODUCT URL
# ==================================================
def clean_product_url(url):

    if not url:
        return ""

    clean_url = url.strip().split("?")[0]

    if "/ref=" in clean_url:
        clean_url = clean_url.split("/ref=")[0]

    if "amazon." in clean_url:
        asin_match = re.search(
            r"/(?:dp|gp/product)/([A-Z0-9]{10})",
            clean_url
        )

        if asin_match:
            return f"https://www.amazon.in/dp/{asin_match.group(1)}"

    return clean_url


# ==================================================
# HELPER: EXTRACT SHORT PRODUCT IDENTITY
# ==================================================
def extract_product_identity(title):

    title = str(title or "")

    title = title.split("|")[0]
    title = title.split(":")[0]
    title = title.split(" with ")[0]
    title = title.split(" With ")[0]

    title = re.sub(r"\([^)]*\)", " ", title)
    title = re.sub(r"[^A-Za-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()

    remove_words = {
        "black", "white", "blue", "green", "red", "yellow", "pink",
        "silver", "gold", "grey", "gray", "storage", "ram", "rom",
        "pack", "combo", "offer", "new", "latest", "original",
        "features", "feature", "powered", "mobile", "phone",
        "wireless", "bluetooth", "truly", "buds", "earbuds"
    }

    words = []

    for word in title.split():

        if word.lower() in remove_words:
            continue

        words.append(word)

        if len(words) >= 5:
            break

    return " ".join(words).strip()


# ==================================================
# HELPER: CREATE BROAD SEARCH QUERY
# ==================================================
def build_broad_search_query(identity_query):

    words = str(identity_query or "").split()

    if len(words) >= 3:
        return " ".join(words[:3])

    return identity_query


# ==================================================
# HELPER: NORMALIZE WORDS
# ==================================================
def normalize_words(text):

    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    stop_words = {
        "with", "and", "for", "the", "from", "this", "that",
        "new", "latest", "original", "official", "pack", "combo",
        "best", "sale", "offer", "discount", "free", "features",
        "feature", "powered", "compatible", "india", "online", "buy",
        "store", "mobile", "phone", "smartphone", "camera", "battery",
        "black", "white", "blue", "green", "red", "yellow", "pink",
        "silver", "gold", "grey", "gray", "wireless", "bluetooth",
        "truly", "earbuds", "buds"
    }

    return {
        word for word in text.split()
        if len(word) > 2 and word not in stop_words
    }


# ==================================================
# HELPER: MATCH SCORE
# ==================================================
def product_match_score(source_title, result_title):

    source_words = normalize_words(source_title)
    result_words = normalize_words(result_title)

    if not source_words or not result_words:
        return 0

    matched = source_words.intersection(result_words)

    return len(matched) / len(source_words)

def detect_product_category(title):
    title = str(title or "").lower()

    if any(w in title for w in ["galaxy", "iphone", "redmi", "realme", "oneplus", "5g", "smartphone"]):
        return "phone"

    if any(w in title for w in ["airdopes", "earbuds", "tws", "buds"]):
        return "earbuds"

    if any(w in title for w in ["rockerz", "headphone", "headphones"]):
        return "headphones"

    if any(w in title for w in ["smartwatch", "smart watch", "colorfit", "fire-boltt", "noise"]):
        return "smartwatch"

    if any(w in title for w in ["power bank", "powerbank", "mah"]):
        return "powerbank"

    return "general"

def is_accessory_product(title):
    title = str(title or "").lower()

    bad_words = [
        "cover", "case", "charger", "adapter", "cable",
        "tempered", "screen guard", "protector", "wallet",
        "skin", "stand", "holder"
    ]

    return any(word in title for word in bad_words)

def extract_phone_model(title):
    title = str(title or "").lower()

    match = re.search(
        r"(galaxy\s+[a-z]?\d+|iphone\s+\d+\s*(plus|pro max|pro)?|redmi\s+[a-z]?\d+\s*(pro)?|realme\s+[a-z]?\d+|oneplus\s+\d+)",
        title
    )

    return match.group(1).strip() if match else ""

def is_valid_url_match(source_title, result_title):
    category = detect_product_category(source_title)

    source = str(source_title or "").lower()
    result = str(result_title or "").lower()

    if is_accessory_product(result):
        return False

    if category == "phone":
        model = extract_phone_model(source)

        # allow S25 FE / S25 / Galaxy S25 variations
        model_words = set(model.split()) if model else set()
        result_words = set(result.split())

        important_model_words = {
            w for w in model_words
            if w not in {"samsung", "galaxy"}
        }

        if important_model_words:
            if not important_model_words.issubset(result_words):
                return False

        if "5g" in source and "5g" not in result:
            return False

        return True

    score = product_match_score(source_title, result_title)

    if category in ["earbuds", "headphones", "smartwatch", "powerbank"]:
        return score >= 0.35

    return score >= 0.20

# ==================================================
# SEARCH PRODUCTS
# URL SEARCH + BROAD CROSS-SITE MATCHING
# ==================================================
@web.route("/search", methods=["GET"])
@login_required
def search_page():

    sub = request.args.get("sub", "").strip()
    query = request.args.get("q", "").strip()

    if not query:
        flash("Please enter a search query.", "warning")
        return redirect(url_for("web.shop"))

    results = []

    try:

        # ==================================================
        # URL SEARCH MODE
        # ==================================================
        if query.startswith("http://") or query.startswith("https://"):

            clean_url = clean_product_url(query)

            print("CLEAN URL:", clean_url)

            main_product = scrape_from_url(clean_url)
            if main_product:

                detected_title = (
                    main_product.get("title")
                    or ""
                )

                if not sub:
                    sub = detect_sub_from_query(
                        detected_title
                    )

            if main_product and float(main_product.get("price") or 0) > 0:

                main_title = (
                    main_product.get("title")
                    or main_product.get("product_name")
                    or ""
                ).strip()

                print("SCRAPED PRODUCT TITLE:", main_title)

                identity_query = extract_product_identity(main_title)

                print("IDENTITY SEARCH QUERY:", identity_query)

                broad_query = build_broad_search_query(identity_query)

                print("BROAD SEARCH QUERY:", broad_query)

                results.append(main_product)

                if broad_query:

                    other_results = search_all_sites(broad_query) or []

                    print("OTHER RESULTS:", len(other_results))

                    accurate_matches = []

                    for item in other_results:

                        if not isinstance(item, dict):
                            continue

                        title = (
                            item.get("title")
                            or item.get("product_name")
                            or ""
                        ).strip()

                        price = float(item.get("price") or 0)

                        url = (
                            item.get("url")
                            or item.get("product_url")
                            or ""
                        ).strip()

                        website = (
                            item.get("website")
                            or item.get("site")
                            or "Unknown"
                        )

                        if not title or title == "N/A":
                            continue

                        if price <= 0 or not url:
                            continue

                        if url.split("?")[0] == clean_url.split("?")[0]:
                            continue

                        if not is_valid_url_match(main_title, title):
                            continue

                        score = product_match_score(main_title, title)
                        item["match_score"] = round(score * 100, 2)
                        item["website"] = website

                        accurate_matches.append(item)

                    website_priority = {
                        "Amazon": 1,
                        "Flipkart": 2,
                        "Snapdeal": 3,
                        "ShopClues": 4
                    }

                    accurate_matches = sorted(
                        accurate_matches,
                        key=lambda x: (
                            website_priority.get(
                                x.get("website"),
                                99
                            ),
                            -x.get("match_score", 0),
                            float(x.get("price") or 0)
                        )
                    )

                    # ==================================================
                    # PRIORITIZE ONE BEST MATCH FROM EACH WEBSITE
                    # ==================================================
                    final_matches = []
                    seen_websites = set()

                    for item in accurate_matches:

                        website = item.get("website", "Unknown")

                        if website not in seen_websites:
                            final_matches.append(item)
                            seen_websites.add(website)

                    # Add extra close matches only after each website gets chance
                    for item in accurate_matches:

                        if item not in final_matches:
                            final_matches.append(item)

                    results.extend(final_matches[:10])

            else:
                flash("Could not scrape product from this URL.", "danger")

        # ==================================================
        # NORMAL TEXT SEARCH MODE
        # ==================================================
        else:

            results = search_all_sites(query) or []

            if not sub:
                sub = detect_sub_from_query(query)

            # REMOVE ACCESSORIES FOR PHONE SEARCHES
            if detect_product_category(query) == "phone":

                bad_words = [
                    "case", "cover", "charger", "cable",
                    "screen guard", "tempered", "protector",
                    "adapter", "wallet", "skin", "holder"
                ]

                results = [
                    item for item in results
                    if not any(
                        word in item.get("title", "").lower()
                        for word in bad_words
                    )
                ]

        # ==================================================
        # FINAL CLEANING + REMOVE DUPLICATES
        # ==================================================
        cleaned = []
        seen_urls = set()

        for item in results:

            if not isinstance(item, dict):
                continue

            title = (
                item.get("title")
                or item.get("product_name")
                or ""
            ).strip()

            # REMOVE ACCESSORIES FOR PHONE SEARCH
            if detect_product_category(query) == "phone":

                bad_words = [
                    "case",
                    "cover",
                    "charger",
                    "cable",
                    "screen guard",
                    "tempered",
                    "protector",
                    "adapter",
                    "wallet",
                    "skin",
                    "holder",
                    "glass",
                    "back cover",
                    "data cable",
                    "usb cable"
                ]

                title_lower = title.lower()

                if any(word in title_lower for word in bad_words):
                    continue

            price = float(item.get("price") or 0)

            url = (
                item.get("url")
                or item.get("product_url")
                or ""
            ).strip()

            website = (
                item.get("website")
                or item.get("site")
                or "Unknown"
            )

            image = (
                item.get("image")
                or "https://via.placeholder.com/300?text=No+Image"
            )

            if not title or title == "N/A":
                continue

            if price <= 0 or not url:
                continue

            clean_item_url = url.split("?")[0]

            if clean_item_url in seen_urls:
                continue

            seen_urls.add(clean_item_url)

            cleaned.append({
                "title": title,
                "product_name": title,
                "price": price,
                "old_price": price,
                "image": image,
                "url": url,
                "product_url": url,
                "website": website,
                "rating": item.get("rating") or 0,
                "reviews": item.get("reviews") or 0,
                "match_score": item.get(
                    "match_score",
                    100 if len(cleaned) == 0 else 0
                ),
                "price_drop_detected": item.get(
                    "price_drop_detected",
                    False
                ),
                "drop_percent": item.get("drop_percent", 0)
            })

        results = cleaned

        log_activity(f"Searched: {query[:200]}")

    except Exception as e:

        print("SEARCH ERROR:", e)

        flash("Search failed.", "danger")

    return render_template(
        "user/search_product.html",
        results=results,
        query=query,
        category="",
        sub="",
        min_price=None,
        max_price=None,
        marketplace=""
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

            link = ProductLink.query.filter_by(
                product_id=existing.product_id,
                url=existing.product_url
            ).first()

            if not link:
                link = ProductLink(
                    product_id=existing.product_id,
                    website=existing.website,
                    url=existing.product_url,
                    current_price=existing.price
                )
                db.session.add(link)
                db.session.flush()

            history = PriceHistory(
                link_id=link.id,
                product_id=existing.product_id,
                old_price=existing.old_price,
                price=existing.price,
                price_change=0,
                change_percent=0,
                website=existing.website,
                checked_at=datetime.now(timezone.utc)
            )

            db.session.add(history)
            db.session.commit()

            flash("Product is now being tracked.", "success")

            return redirect(
                url_for(
                    "web.product_detail",
                    product_id=existing.product_id
                )
            )

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
            image=image,
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
# SAVE PRODUCT
# ==================================================
@web.route("/save-product", methods=["POST"])
@login_required
def save_product_route():

    try:

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

        if not name or not url:

            flash(
                "Invalid product.",
                "danger"
            )

            return redirect(url_for("web.shop"))

        existing = TrackedProduct.query.filter_by(
            user_id=current_user.id,
            product_url=url
        ).first()

        if existing:

            flash(
                "Product already saved/tracked.",
                "warning"
            )

            return redirect(url_for("web.saved"))

        product = Product(
            title=name,
            price=price,
            image=image,
            website=website,
            source=website,
            url=url,
            user_id=current_user.id
        )

        db.session.add(product)
        db.session.flush()

        saved = TrackedProduct(
            user_id=current_user.id,
            product_id=product.id,
            product_name=name,
            image=image,
            website=website,
            price=price,
            target_price=0,
            product_url=url,
            is_active=False
        )

        db.session.add(saved)

        db.session.commit()

        flash(
            "Product saved successfully!",
            "success"
        )

        log_activity(
            f"Saved product: {name}"
        )

        return redirect(url_for("web.saved"))

    except Exception as e:

        db.session.rollback()

        print("SAVE PRODUCT ERROR:", e)

        flash(
            "Could not save product.",
            "danger"
        )

        return redirect(url_for("web.shop"))
    
# ==================================================
# REMOVE SAVED PRODUCT
# ==================================================
@web.route(
    "/remove-saved/<int:tracked_id>",
    methods=["POST"]
)
@login_required
def remove_saved(tracked_id):

    try:

        item = TrackedProduct.query.get_or_404(
            tracked_id
        )

        # SECURITY CHECK
        if item.user_id != current_user.id:

            flash(
                "Unauthorized action.",
                "danger"
            )

            return redirect(
                url_for("web.saved")
            )

        product_name = item.product_name

        db.session.delete(item)

        db.session.commit()

        log_activity(
            f"Removed saved product: {product_name}"
        )

        flash(
            "Saved product removed.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print("REMOVE SAVED ERROR:", e)

        flash(
            "Could not remove product.",
            "danger"
        )

    return redirect(
        url_for("web.saved")
    )
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
    if not is_active:

        smart_insight = (
            "Tracking is currently stopped"
        )

    elif not target_price:

        smart_insight = (
            "No target price set"
        )

    elif current_price <= target_price:

        smart_insight = (
            "Below target price"
        )

    elif price_drop_percent >= 10:

        smart_insight = (
            "Big price drop detected"
        )

    elif trend == "down":

        smart_insight = (
            "Price is moving downward"
        )

    elif trend == "up":

        smart_insight = (
            "Price is increasing"
        )

    else:

        smart_insight = (
            "Still above target price"
        )
    # ==================================================
    # AI INSIGHTS
    # ==================================================
    ai_insights = []

    if not is_active:

        ai_insights.append(
            "Tracking is paused. Scheduler will skip this product."
        )

    if len(history_data) < 2:

        ai_insights.append(
            "Not enough history yet. More checks will improve insights."
        )

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
            "Price is trending downward."
        )

    elif trend == "up":

        ai_insights.append(
            "Price is increasing. You may wait before buying."
        )

    elif trend == "stable" and len(history_data) > 1:

        ai_insights.append(
            "Price is currently stable."
        )

    if not ai_insights:

        ai_insights.append(
            "No major price alert detected."
        )

    # ==================================================
    # TRACKING STATUS
    # ==================================================
    tracking_status = (
        "This product is currently being tracked."
        if is_active else
        "Tracking is currently stopped."
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
    # ML PRICE PREDICTION
    # ==================================================
    predicted_price = predict_next_price(history_data)

    ml_recommendation = "Not enough price history for prediction"

    if predicted_price:

        if predicted_price < current_price:
            ml_recommendation = "Price may decrease. You can wait before buying."

        elif predicted_price > current_price:
            ml_recommendation = "Price may increase. Buying now may be better."

        else:
            ml_recommendation = "Price may remain stable."

    prediction_labels = graph_labels.copy()
    prediction_prices = graph_prices.copy()

    if predicted_price:
        prediction_labels.append("Predicted Next")
        prediction_prices.append(predicted_price)
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

        predicted_price=predicted_price,
        ml_recommendation=ml_recommendation,

        prediction_labels=prediction_labels,
        prediction_prices=prediction_prices,

        target_price=target_price,

        smart_insight=smart_insight,
        tracking_status=tracking_status,

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
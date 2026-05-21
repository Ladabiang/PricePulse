import logging
import re

from app.scrapers.amazon import search_amazon
from app.scrapers.snapdeal import search_snapdeal
from app.scrapers.shopclues import search_shopclues
from app.scrapers.flipkart import search_flipkart
from app.scrapers.url_scraper import scrape_from_url

logger = logging.getLogger("base_scraper")


# ==================================================
# URL CHECK
# ==================================================
def is_url(text: str):
    return isinstance(text, str) and text.startswith(("http://", "https://"))


# ==================================================
# PRICE CLEANER
# ==================================================
def clean_price(value):
    try:
        if not value:
            return 0

        value = str(value).replace("₹", "").replace(",", "")
        match = re.search(r"\d+(\.\d+)?", value)

        return int(float(match.group(0))) if match else 0
    except:
        return 0


# ==================================================
# NORMALIZER (SAFE + ROBUST)
# ==================================================
def normalize(item):
    if not isinstance(item, dict):
        return None

    try:
        title = (item.get("title") or "").strip()
        price = clean_price(item.get("price"))
        image = item.get("image") or ""
        url = item.get("url") or ""
        website = item.get("site") or item.get("website") or "Unknown"

        # rating safe parse
        try:
            rating = float(str(item.get("rating", 0)).replace("⭐", "").strip())
        except:
            rating = 0.0

        # reviews safe parse
        try:
            reviews = str(item.get("reviews", 0)).lower().replace("k", "000")
            reviews = int(float(reviews))
        except:
            reviews = 0

        return {
            "title": title,
            "price": price,
            "image": image,
            "url": url,
            "website": website,
            "rating": rating,
            "reviews": reviews
        }

    except:
        return None

# ==================================================
# REMOVE DUPLICATES (SAFE)
# ==================================================
def deduplicate(items):
    seen = set()
    result = []

    for i in items:
        if not i:
            continue

        url = i.get("url", "").split("?")[0]
        if not url or url in seen:
            continue

        seen.add(url)
        result.append(i)

    return result


# ==================================================
# MAIN ENGINE (FULLY FIXED)
# ==================================================
# ==================================================
# MAIN ENGINE (FULLY FIXED)
# ==================================================
def search_all_sites(query):

    try:
        logger.info(f"Searching: {query}")

        # ==================================================
        # URL MODE
        # ==================================================
        if is_url(query):

            # ==============================================
            # AMAZON SEARCH URL
            # Example:
            # https://amazon.in/s?k=iphone
            # ==============================================
            if "/s?" in query or "/s/" in query:

                match = re.search(r"[?&]k=([^&]+)", query)

                if match:

                    keyword = match.group(1)
                    keyword = keyword.replace("+", " ")

                    logger.info(
                        f"Converted Amazon search URL to keyword: {keyword}"
                    )

                    amazon = search_amazon(keyword) or []

                    normalized = []

                    for item in amazon:
                        n = normalize(item)

                        if n:
                            normalized.append(n)

                    cleaned = [
                        x for x in normalized
                        if x["title"] and x["price"] > 0
                    ]

                    unique = deduplicate(cleaned)

                    return sorted(
                        unique,
                        key=lambda x: x["price"]
                    )

                return []

            # ==============================================
            # PRODUCT URL MODE
            # ==============================================
            result = scrape_from_url(query)

            if not result:
                return []

            if isinstance(result, dict):
                return [result]

            if isinstance(result, list):
                return [
                    r for r in result
                    if isinstance(r, dict)
                ]

            return []

        # ==================================================
        # NORMAL TEXT SEARCH
        # ==================================================
        amazon = search_amazon(query) or []
        snapdeal = search_snapdeal(query) or []
        shopclues = search_shopclues(query) or []
        flipkart = search_flipkart(query) or []

        # ==============================================
        # BALANCED MERGE
        # ==============================================
        combined = (
            amazon[:10] +
            flipkart[:10] +
            snapdeal[:10] +
            shopclues[:10]
        )

        # ==================================================
        # NORMALIZE
        # ==================================================
        normalized = []

        for item in combined:

            n = normalize(item)

            if n:
                normalized.append(n)

        # ==================================================
        # FILTER VALID ITEMS
        # ==================================================
        cleaned = [
            x for x in normalized
            if x["title"] and x["price"] > 0
        ]

        # ==================================================
        # REMOVE DUPLICATES
        # ==================================================
        unique = deduplicate(cleaned)

        # ==================================================
        # SORT BY PRICE
        # ==================================================
        return sorted(
            unique,
            key=lambda x: x["price"]
        )

    except Exception as e:

        logger.error(f"Base scraper error: {e}")

        return []
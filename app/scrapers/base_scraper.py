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
    return isinstance(text, str) and text.startswith(
        ("http://", "https://")
    )


# ==================================================
# PRICE CLEANER
# ==================================================
def clean_price(value):

    try:

        if not value:
            return 0

        value = (
            str(value)
            .replace("₹", "")
            .replace(",", "")
        )

        match = re.search(
            r"\d+(\.\d+)?",
            value
        )

        return (
            int(float(match.group(0)))
            if match else 0
        )

    except:
        return 0


# ==================================================
# NORMALIZER
# ==================================================
def normalize(item):

    if not isinstance(item, dict):
        return None

    try:

        title = (
            item.get("title") or ""
        ).strip()

        price = clean_price(
            item.get("price")
        )

        image = item.get("image") or ""

        url = item.get("url") or ""

        website = (
            item.get("site")
            or item.get("website")
            or "Unknown"
        )

        # ==========================================
        # RATING
        # ==========================================
        try:

            rating = float(
                str(
                    item.get("rating", 0)
                )
                .replace("⭐", "")
                .strip()
            )

        except:
            rating = 0.0

        # ==========================================
        # REVIEWS
        # ==========================================
        try:

            reviews = (
                str(
                    item.get("reviews", 0)
                )
                .lower()
                .replace("k", "000")
            )

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
# REMOVE DUPLICATES
# ==================================================
def deduplicate(items):

    seen = set()

    result = []

    for i in items:

        if not i:
            continue

        url = i.get(
            "url",
            ""
        ).split("?")[0]

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        result.append(i)

    return result


# ==================================================
# MAIN SEARCH ENGINE
# ==================================================
def search_all_sites(query):

    try:

        logger.info(f"Searching: {query}")

        # ==================================================
        # URL MODE
        # ==================================================
        if is_url(query):

            # ==============================================
            # AMAZON SEARCH URL MODE
            # Example: https://www.amazon.in/s?k=iphone
            # ==============================================
            if "/s?" in query or "/s/" in query:

                match = re.search(
                    r"[?&]k=([^&]+)",
                    query
                )

                if not match:
                    return []

                keyword = match.group(1).replace("+", " ")

                logger.info(
                    f"Converted Amazon search URL to keyword: {keyword}"
                )

                try:
                    amazon_results = search_amazon(keyword) or []
                except Exception as e:
                    logger.error(f"Amazon search URL failed: {e}")
                    amazon_results = []

                cleaned = []

                for item in amazon_results:

                    try:
                        n = normalize(item)

                        if not n:
                            continue

                        if not n.get("title"):
                            continue

                        if float(n.get("price") or 0) <= 0:
                            continue

                        if not n.get("url"):
                            continue

                        cleaned.append(n)

                    except Exception as e:
                        logger.error(f"Amazon URL item clean failed: {e}")
                        continue

                return sorted(
                    deduplicate(cleaned),
                    key=lambda x: x["price"]
                )

            # ==============================================
            # DIRECT PRODUCT URL MODE
            # ==============================================
            try:
                result = scrape_from_url(query)
            except Exception as e:
                logger.error(f"Direct URL scrape failed: {e}")
                return []

            if not result:
                return []

            if isinstance(result, dict):

                n = normalize(result)

                if (
                    n
                    and n.get("title")
                    and float(n.get("price") or 0) > 0
                    and n.get("url")
                ):
                    return [n]

                return []

            if isinstance(result, list):

                cleaned = []

                for item in result:

                    try:
                        n = normalize(item)

                        if not n:
                            continue

                        if not n.get("title"):
                            continue

                        if float(n.get("price") or 0) <= 0:
                            continue

                        if not n.get("url"):
                            continue

                        cleaned.append(n)

                    except Exception as e:
                        logger.error(f"URL list item clean failed: {e}")
                        continue

                return deduplicate(cleaned)

            return []

        # ==================================================
        # NORMAL KEYWORD SEARCH MODE
        # ==================================================
        all_results = []

        scrapers = [
            ("Amazon", search_amazon),
            ("Flipkart", search_flipkart),
            ("Snapdeal", search_snapdeal),
            ("ShopClues", search_shopclues),
        ]

        for site_name, scraper_func in scrapers:

            try:

                logger.info(f"{site_name} search started")

                site_results = scraper_func(query) or []

                if not isinstance(site_results, list):
                    logger.warning(
                        f"{site_name} returned non-list result"
                    )
                    continue

                site_cleaned = []

                for item in site_results:

                    try:

                        n = normalize(item)

                        if not n:
                            continue

                        title = n.get("title") or ""
                        price = float(n.get("price") or 0)
                        url = n.get("url") or ""

                        if not title:
                            continue

                        if price <= 0:
                            continue

                        if not url:
                            continue

                        if not n.get("image"):
                            n["image"] = (
                                "https://via.placeholder.com/300?text=No+Image"
                            )

                        if not n.get("website") or n.get("website") == "Unknown":
                            n["website"] = site_name

                        n["rating"] = n.get("rating") or 0
                        n["reviews"] = n.get("reviews") or 0

                        site_cleaned.append(n)

                    except Exception as e:
                        logger.error(
                            f"{site_name} item clean failed: {e}"
                        )
                        continue

                logger.info(
                    f"{site_name} returned {len(site_cleaned)} valid products"
                )

                all_results.extend(site_cleaned)

            except Exception as e:

                logger.error(
                    f"{site_name} scraper failed: {e}"
                )

                continue

        unique = deduplicate(all_results)

        return sorted(
            unique,
            key=lambda x: x["price"]
        )

    except Exception as e:

        logger.error(
            f"Base scraper error: {e}"
        )

        return []
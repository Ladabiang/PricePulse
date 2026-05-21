from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import logging
import time
import re
import json

logger = logging.getLogger("shopclues")

BASE_URL = "https://www.shopclues.com"


# ==================================================
# CLEAN PRICE
# ==================================================
def clean_price(text):
    try:
        if not text:
            return 0

        text = str(text).replace("₹", "").replace(",", "").strip()
        match = re.search(r"\d+(\.\d+)?", text)

        return int(float(match.group())) if match else 0

    except:
        return 0


# ==================================================
# CLEAN FLOAT / INT
# ==================================================
def clean_float(text):
    try:
        if not text:
            return 0.0
        match = re.search(r"\d+(\.\d+)?", str(text))
        return float(match.group()) if match else 0.0
    except:
        return 0.0


def clean_int(text):
    try:
        if not text:
            return 0
        return int(re.sub(r"[^\d]", "", str(text)) or 0)
    except:
        return 0


# ==================================================
# IMAGE EXTRACTOR
# ==================================================
def extract_image(item):

    try:
        data_img = item.get("data-img")

        if data_img:
            try:
                data = json.loads(data_img)

                for key in ["img", "image", "src", "url"]:
                    if data.get(key):
                        img = data[key]

                        if img.startswith("//"):
                            img = "https:" + img

                        return img
            except:
                pass

        img_tag = item.select_one("img")

        if img_tag:
            src = (
                img_tag.get("data-src") or
                img_tag.get("data-original") or
                img_tag.get("src") or
                ""
            )

            if not src or "data:image" in src:
                return "https://via.placeholder.com/300?text=No+Image"

            if src.startswith("//"):
                src = "https:" + src

            if any(x in src.lower() for x in ["logo", "icon", "sprite"]):
                return "https://via.placeholder.com/300?text=No+Image"

            return src

    except:
        pass

    return "https://via.placeholder.com/300?text=No+Image"


# ==================================================
# ⭐ RATING + REVIEWS EXTRACTOR (NEW FIX)
# ==================================================
def extract_rating_reviews(item):

    rating = 0.0
    reviews = 0

    try:
        # ================= RATING =================
        rating_selectors = [
            ".rating",
            ".prod_rating",
            ".star",
            ".rating_value",
            "[class*='rating']"
        ]

        for sel in rating_selectors:
            tag = item.select_one(sel)
            if tag:
                rating = clean_float(tag.get_text())
                if rating > 0:
                    break

        # ================= REVIEWS =================
        review_selectors = [
            ".review",
            ".reviews",
            ".ratingCount",
            ".review-count",
            "[class*='review']"
        ]

        for sel in review_selectors:
            tag = item.select_one(sel)
            if tag:
                text = tag.get_text()
                reviews = clean_int(text)
                if reviews > 0:
                    break

        # fallback: sometimes both are in one text line
        if rating == 0.0 or reviews == 0:
            full_text = item.get_text(" ", strip=True)

            # example: "4.2 (1,234 Reviews)"
            rating_match = re.search(r"(\d+\.\d+)", full_text)
            review_match = re.search(r"(\d[\d,]*)\s*review", full_text.lower())

            if rating_match:
                rating = float(rating_match.group())

            if review_match:
                reviews = clean_int(review_match.group())

    except Exception as e:
        logger.debug(f"Rating parse error: {e}")

    return rating, reviews


# ==================================================
# SAFE TEXT
# ==================================================
def safe_text(tag):
    return tag.get_text(strip=True) if tag else ""


# ==================================================
# MAIN SCRAPER
# ==================================================
def search_shopclues(product):

    url = f"{BASE_URL}/search?q={quote_plus(product)}"
    results = []

    try:
        logger.info(f"[ShopClues] Searching: {product}")

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox"]
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            page = context.new_page()

            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            time.sleep(4)

            for _ in range(3):
                page.mouse.wheel(0, 3000)
                time.sleep(1.5)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        items = (
            soup.select("div.column") or
            soup.select("div.product-tuple-listing") or
            soup.select("div.product_list") or
            soup.select("div.row div")
        )

        if not items:
            logger.warning("[ShopClues] No products found")
            return []

        for item in items[:30]:

            try:
                title_tag = (
                    item.select_one("h2") or
                    item.select_one("a") or
                    item.select_one(".prod_name")
                )

                title = safe_text(title_tag)

                if not title or len(title) < 5:
                    continue

                link_tag = item.select_one("a[href]")
                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                full_url = urljoin(BASE_URL, href)

                price_tag = (
                    item.select_one(".p_price") or
                    item.select_one(".f_price") or
                    item.select_one(".price") or
                    item.select_one("span")
                )

                price = clean_price(price_tag.get_text() if price_tag else "")

                if price <= 0:
                    continue

                image = extract_image(item)

                # ⭐⭐⭐ FIXED HERE ⭐⭐⭐
                rating, reviews = extract_rating_reviews(item)

                results.append({
                    "title": title,
                    "price": price,
                    "image": image,
                    "url": full_url,
                    "site": "ShopClues",
                    "rating": rating,
                    "reviews": reviews
                })

            except Exception as e:
                logger.debug(f"[ShopClues] Skip item: {e}")
                continue

        logger.info(f"[ShopClues] Final results: {len(results)}")
        return results

    except Exception as e:
        logger.error(f"[ShopClues] Error: {e}")
        return []
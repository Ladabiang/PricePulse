import logging
import re
import time
import random
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger("snapdeal")

BASE_URL = "https://www.snapdeal.com"


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
# IMAGE HANDLER
# ==================================================
def extract_image(img_tag):
    if not img_tag:
        return "https://via.placeholder.com/300?text=No+Image"

    src = (
        img_tag.get("src") or
        img_tag.get("data-src") or
        img_tag.get("data-original") or
        ""
    )

    if not src or "data:image" in src:
        return "https://via.placeholder.com/300?text=No+Image"

    if src.startswith("//"):
        src = "https:" + src

    return src


# ==================================================
# CLEAN TITLE
# ==================================================
def clean_title(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text).strip()

    junk_words = ["view details", "quick view", "add to cart"]
    for j in junk_words:
        text = text.replace(j, "")

    return text.strip()


# ==================================================
#  RATING + REVIEWS 
# ==================================================
def extract_rating_reviews(item):

    rating = 0.0
    reviews = 0

    # -----------------------------
    # RATING selectors (Snapdeal varies a lot)
    # -----------------------------
    rating_selectors = [
        "div.rating-stars",
        "span.product-rating",
        "div.filled-stars",
        "span.avrg-rating",
        ".filled-stars"
    ]

    for sel in rating_selectors:
        tag = item.select_one(sel)
        if tag:
            text = tag.get_text(strip=True)
            match = re.search(r"\d+(\.\d+)?", text)
            if match:
                rating = float(match.group())
                break

    # -----------------------------
    # REVIEWS selectors
    # -----------------------------
    review_selectors = [
        "span.product-rating-count",
        "span.rating-count",
        "span.ratingCount",
        ".rating-count",
        ".product-rating-count"
    ]

    for sel in review_selectors:
        tag = item.select_one(sel)
        if tag:
            digits = re.sub(r"[^\d]", "", tag.get_text())
            if digits:
                reviews = int(digits)
                break

    return rating, reviews


# ==================================================
# PRICE EXTRACTOR
# ==================================================
def extract_price(item):
    selectors = [
        "span.product-price",
        "span.payBlkBig",
        "span.lfloat.product-price",
        "span.price",
    ]

    for sel in selectors:
        tag = item.select_one(sel)
        if tag:
            price = clean_price(tag.get_text())
            if price > 0:
                return price

    return 0


# ==================================================
# MAIN SCRAPER
# ==================================================
def search_snapdeal(product):

    url = f"{BASE_URL}/search?keyword={quote_plus(product)}"
    results = []

    try:
        logger.info(f"[Snapdeal] Searching: {product}")

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                slow_mo=300,
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

            context.add_init_script("""

                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1,2,3,4,5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            """)

            page = context.new_page()
            page.set_default_timeout(8000)
            page.goto(
                url,
                wait_until="commit",
                timeout=15000
            )

            page.wait_for_timeout(1500)

            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(1000)

            html = page.content()
            browser.close()

        print(html[:2000])
        soup = BeautifulSoup(html, "html.parser")


        items = soup.select("div.product-tuple-listing")
        if not items:
            items = soup.select("div.product-tuple-description")

        if not items:
            logger.warning("[Snapdeal] No products found")
            return []

        for item in items[:30]:

            try:
                title_tag = item.select_one("p.product-title") or item.select_one("a.dp-widget-link")
                title = clean_title(title_tag.get_text(" ", strip=True) if title_tag else "")

                link_tag = item.select_one("a.dp-widget-link")
                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                full_url = href if href.startswith("http") else BASE_URL + href

                price = extract_price(item)

                img_tag = item.select_one("img")
                image = extract_image(img_tag)

                # NEW: rating + reviews
                rating, reviews = extract_rating_reviews(item)

                if not title or price <= 0:
                    continue

                results.append({
                    "title": title,
                    "price": price,
                    "image": image,
                    "url": full_url,
                    "site": "Snapdeal",
                    "rating": rating,
                    "reviews": reviews
                })

            except Exception as e:
                logger.debug(f"[Snapdeal] Skip item: {e}")
                continue

        logger.info(f"[Snapdeal] Final products: {len(results)}")
        return results

    except Exception as e:
        logger.error(f"[Snapdeal] Crash: {e}")
        return []
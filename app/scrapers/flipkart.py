# =========================================================
# FILE: scrapers/flipkart.py
# FINAL ADVANCED FLIPKART SCRAPER
# =========================================================

import logging
import time
import random
import re

from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("flipkart")

BASE_URL = "https://www.flipkart.com"


# =========================================================
# HELPERS
# =========================================================

def safe_text(tag):

    try:
        return tag.get_text(strip=True)
    except:
        return ""


def clean_price(text):

    try:

        if not text:
            return 0

        text = (
            str(text)
            .replace("₹", "")
            .replace(",", "")
            .strip()
        )

        match = re.search(r"\d+", text)

        return int(match.group()) if match else 0

    except:
        return 0


def clean_image(src):

    if not src:
        return "https://via.placeholder.com/300?text=No+Image"

    src = src.strip()

    if src.startswith("//"):
        src = "https:" + src

    if src.startswith("/"):
        src = BASE_URL + src

    if src.startswith("data:image"):
        return "https://via.placeholder.com/300?text=No+Image"

    return src


def extract_rating(text):

    try:

        if not text:
            return 0.0

        match = re.search(r"\d+(\.\d+)?", text)

        return float(match.group()) if match else 0.0

    except:
        return 0.0


def is_blocked(html):

    html = html.lower()

    blocked_words = [

        "captcha",
        "access denied",
        "robot",
        "security check",
        "blocked",
        "verify you are human"
    ]

    return any(word in html for word in blocked_words)


# =========================================================
# PLAYWRIGHT PAGE
# =========================================================

def create_page():

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(

        headless=False,

        args=[

            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
    )

    context = browser.new_context(

        viewport={
            "width": 1366,
            "height": 768
        },

        locale="en-IN",

        user_agent=(

            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    )

    page = context.new_page()

    # =====================================================
    # STEALTH
    # =====================================================

    page.add_init_script("""

        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        window.chrome = {
            runtime: {}
        };

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1,2,3,4]
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

    """)

    return playwright, browser, page


# =========================================================
# SCRAPE SINGLE PRODUCT
# =========================================================

def scrape_flipkart_product(url):

    try:

        playwright, browser, page = create_page()

        logger.info(f"Opening Flipkart URL: {url}")

        page.goto(

            url,
            timeout=120000,
            wait_until="domcontentloaded"
        )

        # =================================================
        # HUMAN DELAY
        # =================================================

        time.sleep(random.uniform(8, 12))

        # =================================================
        # CLOSE LOGIN POPUP
        # =================================================

        try:

            close_btn = page.locator("button._2KpZ6l._2doB4z")

            if close_btn.count() > 0:

                close_btn.first.click()

                time.sleep(2)

        except:
            pass

        # =================================================
        # WAIT FOR PRODUCT CONTENT
        # =================================================

        try:

            page.wait_for_selector(

                "h1, span.VU-ZEz, span.B_NuCI",
                timeout=30000
            )

        except:
            logger.warning("Product title selector timeout")

        # =================================================
        # HUMAN ACTIVITY
        # =================================================

        page.mouse.move(300, 400)
        time.sleep(1)

        page.mouse.move(600, 500)
        time.sleep(1)

        page.mouse.wheel(0, 2000)
        time.sleep(2)

        page.mouse.wheel(0, 1500)
        time.sleep(2)

        page.mouse.wheel(0, -800)
        time.sleep(2)

        # EXTRA WAIT FOR JS CONTENT
        time.sleep(random.uniform(5, 8))

        html = page.content()

        # DEBUG SAVE

        with open(
            "flipkart_product_debug.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

        browser.close()
        playwright.stop()

        # =================================================
        # CAPTCHA CHECK
        # =================================================

        if is_blocked(html):

            logger.warning("Flipkart blocked request")

            return {

                "title": "Blocked by Flipkart",
                "price": 0,
                "image": "https://via.placeholder.com/300?text=Blocked",
                "rating": 0.0,
                "reviews": "0",
                "url": url,
                "website": "Flipkart"
            }

        soup = BeautifulSoup(html, "html.parser")

        # =================================================
        # TITLE
        # =================================================

        title = "N/A"

        title_selectors = [

            "h1.v1zwn21l",
            "h1[class*='v1zwn']",
            "span.VU-ZEz",
            "span.B_NuCI",
            "h1 span",
            "h1"
        ]

        for selector in title_selectors:

            tag = soup.select_one(selector)

            if tag:

                text = safe_text(tag)

                if len(text) > 3:

                    title = text
                    break

        logger.info(f"TITLE FOUND: {title}")

        # =================================================
        # PRICE
        # =================================================

        price = 0

        price_selectors = [

            "div.Nx9bqj.CxhGGd",
            "div.Nx9bqj",
            "div._30jeq3",
            "div._16Jk6d"
        ]

        for selector in price_selectors:

            tag = soup.select_one(selector)

            if tag:

                price = clean_price(
                    safe_text(tag)
                )

                if price > 0:
                    break

        logger.info(f"PRICE FOUND: {price}")

        # =================================================
        # IMAGE
        # =================================================

        image = ""

        image_selectors = [

            "img.DByuf4",
            "img._396cs4",
            "img"
        ]

        for selector in image_selectors:

            tag = soup.select_one(selector)

            if tag:

                image = (

                    tag.get("src")
                    or tag.get("data-src")
                    or tag.get("srcset")
                    or tag.get("data-srcset")
                    or ""
                )

                image = clean_image(image)

                if image:
                    break

        logger.info(f"IMAGE FOUND: {image}")

        # =================================================
        # RATING
        # =================================================

        rating = 0.0

        rating_selectors = [

            "div.css-146c3p1",
            "div.XQDdHH",
            "div._3LWZlK"
        ]

        for selector in rating_selectors:

            tag = soup.select_one(selector)

            if tag:

                rating = extract_rating(
                    safe_text(tag)
                )

                if 0 < rating <= 5:
                    break

        # =================================================
        # FALLBACK RATING SEARCH
        # =================================================

        if rating == 0.0:

            possible_tags = soup.find_all(
                ["div", "span"]
            )

            for tag in possible_tags:

                text = safe_text(tag)

                match = re.search(
                    r"([0-5]\.?[0-9]?)",
                    text
                )

                if match:

                    value = float(match.group())

                    if 0 < value <= 5:

                        rating = value
                        break

        logger.info(f"RATING FOUND: {rating}")

        # =================================================
        # REVIEWS
        # =================================================

        reviews = "0"

        review_selectors = [

            "span.Wphh3N",
            "span._2_R_DZ"
        ]

        for selector in review_selectors:

            tag = soup.select_one(selector)

            if tag:

                reviews = safe_text(tag)

                if reviews:
                    break

        logger.info(f"REVIEWS FOUND: {reviews}")

        # =================================================
        # FINAL PRODUCT
        # =================================================

        product = {

            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
            "url": url,
            "website": "Flipkart"
        }

        logger.info(f"FLIPKART PRODUCT: {product}")

        return product

    except Exception as e:

        logger.error(f"Flipkart scrape failed: {e}")

        return {

            "title": "N/A",
            "price": 0,
            "image": "https://via.placeholder.com/300?text=No+Image",
            "rating": 0.0,
            "reviews": "0",
            "url": url,
            "website": "Flipkart"
        }


# =========================================================
# SEARCH FLIPKART PRODUCTS
# =========================================================

def search_flipkart(query):

    products = []

    try:

        logger.info(f"[Flipkart] Searching: {query}")

        search_url = (
            f"https://www.flipkart.com/search?q="
            f"{quote_plus(query)}"
        )

        playwright, browser, page = create_page()

        logger.info(f"[Flipkart] Opening Search URL: {search_url}")

        page.goto(

            search_url,
            timeout=120000,
            wait_until="domcontentloaded"
        )

        # =================================================
        # HUMAN DELAY
        # =================================================

        time.sleep(random.uniform(8, 12))

        # =================================================
        # CLOSE LOGIN POPUP
        # =================================================

        try:

            close_btn = page.locator("button._2KpZ6l._2doB4z")

            if close_btn.count() > 0:

                close_btn.first.click()

                time.sleep(2)

        except:
            pass

        # =================================================
        # HUMAN ACTIVITY
        # =================================================

        page.mouse.move(300, 400)
        time.sleep(1)

        page.mouse.move(700, 500)
        time.sleep(1)

        page.mouse.wheel(0, 2500)
        time.sleep(3)

        page.mouse.wheel(0, 1500)
        time.sleep(3)

        html = page.content()

        browser.close()
        playwright.stop()

        # =================================================
        # CAPTCHA CHECK
        # =================================================

        if is_blocked(html):

            logger.warning("[Flipkart] CAPTCHA BLOCKED")

            return []

        soup = BeautifulSoup(html, "html.parser")

        containers = soup.select("div[data-id]")

        logger.info(f"[Flipkart] Containers found: {len(containers)}")

        for item in containers[:30]:

            try:

                title = "N/A"
                price = 0
                image = ""
                rating = 0.0
                reviews = "0"
                url = ""

                # =========================================
                # TITLE
                # =========================================

                title_tag = (

                    item.select_one("div.KzDlHZ")
                    or item.select_one("a.WKTcLC")
                    or item.select_one("div._4rR01T")
                )

                if title_tag:
                    title = safe_text(title_tag)

                # =========================================
                # PRICE
                # =========================================

                price_tag = (

                    item.select_one("div.Nx9bqj")
                    or item.select_one("div._30jeq3")
                )

                if price_tag:
                    price = clean_price(
                        safe_text(price_tag)
                    )

                # =========================================
                # IMAGE
                # =========================================

                image_tag = item.select_one("img")

                if image_tag:

                    image = (

                        image_tag.get("src")
                        or image_tag.get("data-src")
                        or ""
                    )

                    image = clean_image(image)

                # =========================================
                # RATING
                # =========================================

                rating_tag = (

                    item.select_one("div.XQDdHH")
                    or item.select_one("div.css-146c3p1")
                )

                if rating_tag:

                    rating = extract_rating(
                        safe_text(rating_tag)
                    )

                # =========================================
                # URL
                # =========================================

                link_tag = item.select_one("a")

                if link_tag:

                    href = link_tag.get("href", "")

                    if href.startswith("/"):

                        url = BASE_URL + href

                # =========================================
                # SAVE
                # =========================================

                if title != "N/A":

                    products.append({

                        "title": title,
                        "price": price,
                        "image": image,
                        "rating": rating,
                        "reviews": reviews,
                        "url": url,
                        "website": "Flipkart"
                    })

            except Exception as e:

                logger.warning(f"[Flipkart] Product parse error: {e}")

        logger.info(f"[Flipkart] Final products: {len(products)}")

        return products

    except Exception as e:

        logger.error(f"[Flipkart] Search failed: {e}")

        return []
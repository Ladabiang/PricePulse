import logging
import time
import random
import re
import json
import sqlite3

from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

# =========================================================
# LOGGER
# =========================================================
logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("amazon_scraper")

# =========================================================
# CONFIG
# =========================================================
BASE_URL = "https://www.amazon.in"

DB_NAME = "amazon_products.db"

HEADLESS = True

MAX_PRODUCTS = 30

# =========================================================
# USER AGENTS
# =========================================================
USER_AGENTS = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36",

    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
]

# =========================================================
# SQLITE INIT
# =========================================================
def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS products (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        price INTEGER,

        image TEXT,

        rating REAL,

        reviews INTEGER,

        url TEXT UNIQUE,

        website TEXT
    )

    """)

    conn.commit()

    conn.close()

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
            .replace("Rs.", "")
            .replace("INR", "")
            .strip()
        )

        match = re.search(r"\d+(\.\d+)?", text)

        if match:
            return int(float(match.group()))

        return 0

    except:
        return 0


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

        return int(
            re.sub(r"[^\d]", "", str(text))
            or 0
        )

    except:
        return 0

# =========================================================
# CAPTCHA DETECTION
# =========================================================
def is_blocked(html):

    html = html.lower()

    blocked_words = [

        "captcha",
        "robot check",
        "enter the characters",
        "automated access",
        "type the characters",
        "sorry, we just need to make sure"
    ]

    return any(word in html for word in blocked_words)

# =========================================================
# CLEAN AMAZON URL
# =========================================================
def clean_amazon_url(url):

    try:

        url = url.strip()

        url = url.split("?")[0]

        if "/ref=" in url:
            url = url.split("/ref=")[0]

        match = re.search(
            r"/(?:dp|gp/product)/([A-Z0-9]{10})",
            url
        )

        if match:

            asin = match.group(1)

            clean_url = f"{BASE_URL}/dp/{asin}"

            logger.info(f"CLEAN URL: {clean_url}")

            return clean_url

        return url

    except Exception as e:

        logger.error(f"URL CLEAN ERROR: {e}")

        return url

# =========================================================
# SAVE JSON
# =========================================================
def save_json(data, filename="products.json"):

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        logger.info(f"Saved JSON -> {filename}")

    except Exception as e:

        logger.error(f"JSON ERROR: {e}")

# =========================================================
# SQLITE SAVE
# =========================================================
def save_to_sqlite(products):

    try:

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        for product in products:

            try:

                cursor.execute("""

                INSERT OR REPLACE INTO products (

                    title,
                    price,
                    image,
                    rating,
                    reviews,
                    url,
                    website

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

                """, (

                    product["title"],
                    product["price"],
                    product["image"],
                    product["rating"],
                    product["reviews"],
                    product["url"],
                    product["website"]
                ))

            except Exception as e:

                logger.error(f"SQL INSERT ERROR: {e}")

        conn.commit()

        conn.close()

        logger.info("Saved to SQLite")

    except Exception as e:

        logger.error(f"SQLITE ERROR: {e}")

# =========================================================
# LOAD PAGE
# =========================================================
def load_page(url, retries=3):

    for attempt in range(retries):

        browser = None

        try:

            with sync_playwright() as p:

                browser = p.chromium.launch(

                    headless=HEADLESS,

                    channel="chrome",

                    args=[

                        "--disable-blink-features=AutomationControlled",

                        "--disable-dev-shm-usage",

                        "--no-sandbox",

                        "--start-maximized"
                    ]
                )

                context = browser.new_context(

                    viewport={
                        "width": 1366,
                        "height": 768
                    },

                    locale="en-IN",

                    java_script_enabled=True,

                    ignore_https_errors=True,

                    user_agent=random.choice(USER_AGENTS)
                )

                # =================================================
                # STEALTH
                # =================================================
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

                logger.info(f"Opening: {url}")

                page.goto(

                    url,

                    wait_until="domcontentloaded",

                    timeout=120000
                )

                # =================================================
                # WAIT
                # =================================================
                page.wait_for_timeout(
                    random.randint(4000, 7000)
                )

                # =================================================
                # HUMAN SCROLL
                # =================================================
                for _ in range(random.randint(4, 7)):

                    page.mouse.wheel(

                        0,

                        random.randint(1200, 3000)
                    )

                    time.sleep(
                        random.uniform(1, 2)
                    )

                page.wait_for_timeout(3000)

                html = page.content()

                with open(
                    "amazon_debug.html",
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(html)

                if is_blocked(html):

                    logger.warning("Amazon CAPTCHA detected")

                    continue

                return html

        except PlaywrightTimeoutError:

            logger.error("Timeout")

        except Exception as e:

            logger.error(f"LOAD PAGE ERROR: {e}")

        finally:

            try:

                if browser:
                    browser.close()

            except:
                pass

        time.sleep(random.uniform(2, 5))

    return ""

# =========================================================
# PARSE SEARCH RESULTS
# =========================================================
def parse_search_results(soup):

    results = []

    seen = set()

    items = soup.select(
        'div[data-component-type="s-search-result"]'
    )

    logger.info(f"Found containers: {len(items)}")

    for item in items[:MAX_PRODUCTS]:

        try:

            asin = item.get("data-asin", "").strip()

            if not asin:
                continue

            product_url = clean_amazon_url(
                f"{BASE_URL}/dp/{asin}"
            )

            if product_url in seen:
                continue

            seen.add(product_url)

            # =================================================
            # TITLE
            # =================================================
            title = "N/A"

            title_selectors = [

                "h2 span",

                "h2.a-size-mini span",

                ".a-size-base-plus"
            ]

            for selector in title_selectors:

                tag = item.select_one(selector)

                if tag:

                    title = safe_text(tag)

                    if title:
                        break

            if title == "N/A":
                continue

            # =================================================
            # PRICE
            # =================================================
            price = 0

            price_selectors = [

                ".a-price .a-offscreen",

                ".a-price-whole",

                "span.a-price"
            ]

            for selector in price_selectors:

                tag = item.select_one(selector)

                if tag:

                    price = clean_price(
                        safe_text(tag)
                    )

                    if price > 0:
                        break

            if price <= 0:
                continue

            # =================================================
            # IMAGE
            # =================================================
            image = ""

            image_tag = item.select_one(
                "img.s-image"
            )

            if image_tag:

                image = (
                    image_tag.get("src")
                    or image_tag.get("data-src")
                    or ""
                )

            # =================================================
            # RATING
            # =================================================
            rating = 0.0

            rating_tag = item.select_one(
                "span.a-icon-alt"
            )

            if rating_tag:

                rating = clean_float(
                    safe_text(rating_tag)
                )

            # =================================================
            # REVIEWS
            # =================================================
            reviews = 0

            review_selectors = [

                "span.a-size-base.s-underline-text",

                "span[aria-label*='ratings']"
            ]

            for selector in review_selectors:

                tag = item.select_one(selector)

                if tag:

                    reviews = clean_int(
                        safe_text(tag)
                    )

                    if reviews > 0:
                        break

            results.append({

                "title": title,

                "price": price,

                "image": image or "https://via.placeholder.com/300",

                "rating": rating,

                "reviews": reviews,

                "url": product_url,

                "website": "Amazon"
            })

        except Exception as e:

            logger.error(f"ITEM ERROR: {e}")

    return results

# =========================================================
# SEARCH AMAZON
# =========================================================
def search_amazon(keyword):

    try:

        keyword = keyword.strip()

        search_url = (
            f"{BASE_URL}/s?k={quote_plus(keyword)}"
        )

        logger.info(f"SEARCH URL: {search_url}")

        html = load_page(search_url)

        if not html:
            return []

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        results = parse_search_results(soup)

        logger.info(
            f"TOTAL PRODUCTS: {len(results)}"
        )

        save_to_sqlite(results)

        save_json(results)

        return results

    except Exception as e:

        logger.error(f"SEARCH ERROR: {e}")

        return []

# =========================================================
# PRODUCT PAGE SCRAPER
# =========================================================
def scrape_product(url):

    try:

        url = clean_amazon_url(url)

        logger.info(f"Opening product: {url}")

        html = load_page(url)

        if not html:
            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # =================================================
        # TITLE
        # =================================================
        title = "N/A"

        title_selectors = [

            "#productTitle",

            "span#productTitle",

            "h1 span"
        ]

        for selector in title_selectors:

            tag = soup.select_one(selector)

            if tag:

                title = safe_text(tag)

                if title:
                    break

        # =================================================
        # PRICE
        # =================================================
        price = 0

        price_selectors = [

            "span.a-price span.a-offscreen",

            "#corePrice_feature_div span.a-offscreen",

            "#corePriceDisplay_desktop_feature_div span.a-offscreen",

            ".reinventPricePriceToPayMargin span.a-offscreen",

            ".apexPriceToPay span.a-offscreen",

            ".aok-offscreen",

            "span.a-price-whole"
        ]

        for selector in price_selectors:

            tags = soup.select(selector)

            for tag in tags:

                price_text = (

                    tag.get("content", "")

                    or safe_text(tag)
                )

                extracted_price = clean_price(
                    price_text
                )

                if extracted_price > 0:

                    price = extracted_price

                    break

            if price > 0:
                break

        # =================================================
        # IMAGE
        # =================================================
        image = ""

        image_selectors = [

            "#landingImage",

            "#imgTagWrapperId img",

            "img.a-dynamic-image"
        ]

        for selector in image_selectors:

            tag = soup.select_one(selector)

            if tag:

                image = (

                    tag.get("data-old-hires")

                    or tag.get("src")

                    or ""
                )

                if image:
                    break

        # =================================================
        # RATING
        # =================================================
        rating = 0.0

        rating_selectors = [

            "#acrPopover span.a-icon-alt",

            "span.a-icon-alt"
        ]

        for selector in rating_selectors:

            tag = soup.select_one(selector)

            if tag:

                rating = clean_float(
                    safe_text(tag)
                )

                if rating > 0:
                    break

        # =================================================
        # REVIEWS
        # =================================================
        reviews = 0

        review_selectors = [

            "#acrCustomerReviewText",

            "span[data-hook='total-review-count']"
        ]

        for selector in review_selectors:

            tag = soup.select_one(selector)

            if tag:

                reviews = clean_int(
                    safe_text(tag)
                )

                if reviews > 0:
                    break

        # =================================================
        # VALIDATION
        # =================================================
        if title == "N/A" or price <= 0:

            logger.warning(
                "Invalid product page scraped"
            )

            return None

        product = {

            "title": title,

            "price": price,

            "image": image or "https://via.placeholder.com/300",

            "rating": rating,

            "reviews": reviews,

            "url": url,

            "website": "Amazon"
        }

        logger.info("PRODUCT SCRAPED SUCCESSFULLY")

        print(json.dumps(product, indent=4))

        return product

    except Exception as e:

        logger.error(f"PRODUCT ERROR: {e}")

        return None

# =========================================================
# SMART SCRAPER
# =========================================================
def scrape_amazon(query):

    query = query.strip()

    if "amazon." in query and "/dp/" in query:

        product = scrape_product(query)

        return [product] if product else []

    return search_amazon(query)

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    init_db()

    print("\n==============================")
    print(" AMAZON PROFESSIONAL SCRAPER ")
    print("==============================\n")

    query = input(
        "Enter keyword or Amazon URL: "
    )

    results = scrape_amazon(query)

    print("\n==============================")
    print(" RESULTS ")
    print("==============================\n")

    for idx, item in enumerate(results[:10], start=1):

        print(f"{idx}. {item['title']}")

        print(f"Price   : ₹{item['price']}")

        print(f"Rating  : {item['rating']}")

        print(f"Reviews : {item['reviews']}")

        print(f"URL     : {item['url']}")

        print()
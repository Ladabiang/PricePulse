import logging
import random
import re
import time
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger("flipkart")

BASE_URL = "https://www.flipkart.com"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/300?text=No+Image"


# ==================================================
# HELPERS
# ==================================================
def safe_text(tag):
    try:
        return tag.get_text(" ", strip=True) if tag else ""
    except:
        return ""


def clean_price(text):
    try:
        text = str(text or "").replace("₹", "").replace(",", "").strip()
        match = re.search(r"\d+", text)
        return int(match.group()) if match else 0
    except:
        return 0


def clean_image(src):
    if not src:
        return PLACEHOLDER_IMAGE

    src = src.strip()

    if src.startswith("//"):
        src = "https:" + src

    if src.startswith("/"):
        src = BASE_URL + src

    if src.startswith("data:image"):
        return PLACEHOLDER_IMAGE

    return src


def extract_rating(text):
    try:
        match = re.search(r"\d+(\.\d+)?", str(text or ""))
        return float(match.group()) if match else 0.0
    except:
        return 0.0


def clean_reviews(text):
    try:
        text = str(text or "")
        digits = re.sub(r"[^\d]", "", text)
        return digits if digits else "0"
    except:
        return "0"


def is_blocked(html):
    html = str(html or "").lower()

    blocked_words = [
        "captcha",
        "access denied",
        "robot",
        "security check",
        "verify you are human",
        "unusual traffic"
    ]

    return any(word in html for word in blocked_words)


def first_valid_price_from_text(text):
    matches = re.findall(r"₹\s?[\d,]+", str(text or ""))

    for m in matches:
        price = clean_price(m)
        if price > 0:
            return price

    return 0


# ==================================================
# OPEN FLIPKART PAGE
# ==================================================
def open_flipkart_page(url):
    html = ""

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            java_script_enabled=True,
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/135.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/134.0 Safari/537.36"
            ])
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = { runtime: {} };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-IN', 'en-US', 'en']
            });
        """)

        page = context.new_page()
        page.set_default_timeout(20000)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )
        except PlaywrightTimeoutError:
            logger.warning("[Flipkart] Timeout, reading partial HTML")

        page.wait_for_timeout(6000)

        try:
            close_btns = [
                "button._2KpZ6l._2doB4z",
                "button._30XB9F",
                "button[class*='_2KpZ6l']"
            ]

            for selector in close_btns:
                btn = page.locator(selector)
                if btn.count() > 0:
                    btn.first.click(timeout=1500)
                    break
        except:
            pass

        try:
            for _ in range(3):
                page.mouse.wheel(0, random.randint(1000, 1800))
                time.sleep(random.uniform(0.5, 1.2))
        except:
            pass

        try:
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight)
            """)
            page.wait_for_timeout(3000)
        except:
            pass

        html = page.content()

        browser.close()

    return html


# ==================================================
# PARSE SEARCH ITEM
# ==================================================
def parse_search_item(item):
    try:
        link_tag = (
            item.select_one("a.CGtC98")
            or item.select_one("a._1fQZEK")
            or item.select_one("a.IRpwTa")
            or item.select_one("a.s1Q9rs")
            or item.select_one("a[href]")
        )

        if not link_tag:
            return None

        href = link_tag.get("href") or ""
        product_url = urljoin(BASE_URL, href)

        title_tag = (
            item.select_one("div.KzDlHZ")
            or item.select_one("div._4rR01T")
            or item.select_one("a.IRpwTa")
            or item.select_one("a.s1Q9rs")
            or item.select_one("a.WKTcLC")
            or item.select_one("a[title]")
            or link_tag
        )

        title = ""
        if title_tag:
            title = title_tag.get("title") or safe_text(title_tag)

        if not title and link_tag:
            title = link_tag.get("title") or safe_text(link_tag)

        price_tag = (
            item.select_one("div.Nx9bqj")
            or item.select_one("div._30jeq3")
            or item.select_one("div._30jeq3._1_WHN1")
            or item.select_one("div.CEmiEU")
            or item.select_one("div.yRaY8j")
            or item.select_one("div[class*='Nx9bqj']")
            or item.select_one("div[class*='_30jeq3']")
        )

        price = clean_price(safe_text(price_tag)) if price_tag else 0

        if price <= 0:
            price = first_valid_price_from_text(item.get_text(" ", strip=True))

        image_tag = (
            item.select_one("img.DByuf4")
            or item.select_one("img._396cs4")
            or item.select_one("img._53J4C-")
            or item.select_one("img")
        )

        image = PLACEHOLDER_IMAGE

        if image_tag:
            image = clean_image(
                image_tag.get("src")
                or image_tag.get("data-src")
                or image_tag.get("loading")
                or ""
            )

        # =========================
        # RATING + REVIEWS FALLBACK
        # =========================
        full_text = item.get_text(" ", strip=True)

        rating = 0.0
        reviews = "0"

        rating_match = re.search(r"(\d\.\d)", full_text)

        if rating_match:
            rating = float(rating_match.group(1))

        review_match = re.search(
            r"([\d,]+)\s*(Ratings|Rating|Reviews|Review)",
            full_text,
            re.IGNORECASE
        )

        if review_match:
            reviews = review_match.group(1).replace(",", "")

        if not title or title == "N/A":
            return None

        if price <= 0:
            return None

        if not product_url:
            return None
        logger.info(
            f"[Flipkart] "
            f"Rating={rating} "
            f"Reviews={reviews} "
            f"Title={title[:40]}"
        )
        logger.info(f"[Flipkart DEBUG] TEXT={full_text[:300]}")
        logger.info(f"[Flipkart DEBUG] Rating={rating}, Reviews={reviews}")
        return {
            "title": title,
            "price": price,
            "old_price": price,
            "image": image,
            "url": product_url,
            "website": "Flipkart",
            "rating": rating,
            "reviews": reviews
        }

    except Exception as e:
        logger.debug(f"[Flipkart] Item parse error: {e}")
        return None


# ==================================================
# SEARCH FLIPKART
# ==================================================
def search_flipkart(query):
    results = []

    try:
        logger.info(f"[Flipkart] Searching: {query}")

        search_url = f"{BASE_URL}/search?q={quote_plus(query)}"

        logger.info(f"[Flipkart] Opening Search URL: {search_url}")

        html = open_flipkart_page(search_url)

        if not html:
            logger.warning("[Flipkart] Empty HTML")
            return []

        if is_blocked(html):
            logger.warning("[Flipkart] Blocked or captcha detected")
            return []

        soup = BeautifulSoup(html, "html.parser")

        product_blocks = (
            soup.select("div[data-id]")
            or soup.select("div._1AtVbE")
            or soup.select("div.cPHDOP")
            or soup.select("div.slAVV4")
        )

        logger.info(f"[Flipkart] Found containers: {len(product_blocks)}")

        seen_urls = set()

        for item in product_blocks[:30]:

            parsed = parse_search_item(item)

            if not parsed:
                continue

            clean_url = parsed["url"].split("?")[0]

            if clean_url in seen_urls:
                continue

            seen_urls.add(clean_url)

            results.append(parsed)

        logger.info(f"[Flipkart] Final results: {len(results)}")

        return results

    except Exception as e:
        logger.error(f"[Flipkart] ERROR: {e}")
        return results


# ==================================================
# SCRAPE DIRECT FLIPKART PRODUCT URL
# ==================================================
def scrape_flipkart_product(url):
    try:
        logger.info(f"[Flipkart] Opening Product URL: {url}")

        html = open_flipkart_page(url)

        if not html:
            return None

        if is_blocked(html):
            logger.warning("[Flipkart] Product page blocked")
            return None

        soup = BeautifulSoup(html, "html.parser")

        title_tag = (
            soup.select_one("span.VU-ZEz")
            or soup.select_one("span.B_NuCI")
            or soup.select_one("h1 span")
            or soup.select_one("h1")
        )

        title = safe_text(title_tag) if title_tag else "N/A"

        price_tag = (
            soup.select_one("div.Nx9bqj.CxhGGd")
            or soup.select_one("div.Nx9bqj")
            or soup.select_one("div._30jeq3._16Jk6d")
            or soup.select_one("div._30jeq3")
            or soup.select_one("div._16Jk6d")
            or soup.select_one("div.CEmiEU")
        )

        price = clean_price(safe_text(price_tag)) if price_tag else 0

        if price <= 0:
            price = first_valid_price_from_text(soup.get_text(" ", strip=True))

        image_tag = (
            soup.select_one("img.DByuf4")
            or soup.select_one("img._396cs4")
            or soup.select_one("img._53J4C-")
            or soup.select_one("img")
        )

        image = PLACEHOLDER_IMAGE

        if image_tag:
            image = clean_image(
                image_tag.get("src")
                or image_tag.get("data-src")
                or ""
            )

        rating = 0.0

        for selector in [
            "div.XQDdHH",
            "div._3LWZlK",
            "div[class*='XQDdHH']",
            "div[class*='_3LWZlK']"
        ]:

            tag = soup.select_one(selector)

            if tag:

                rating = extract_rating(
                    safe_text(tag)
                )

                if rating > 0:
                    break


        reviews = "0"

        for selector in [
            "span.Wphh3N",
            "span._2_R_DZ",
            "span[class*='Wphh3N']",
            "span[class*='_2_R_DZ']"
        ]:

            tag = soup.select_one(selector)

            if tag:

                reviews = clean_reviews(
                    safe_text(tag)
                )

                if reviews != "0":
                    break

        if title == "N/A" or price <= 0:
            logger.warning("[Flipkart] Product scrape failed")
            return None

        return {
            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
            "url": url,
            "website": "Flipkart"
        }

    except Exception as e:
        logger.error(f"[Flipkart] Product scrape failed: {e}")
        return None
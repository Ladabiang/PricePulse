
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import random
import re


# ==================================================
# CLEANERS
# ==================================================
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
        return int(float(match.group())) if match else 0

    except:
        return 0


def clean_image(src):
    if not src:
        return "https://via.placeholder.com/300?text=No+Image"

    src = src.strip()

    if src.startswith("//"):
        return "https:" + src

    if src.startswith("data:image"):
        return "https://via.placeholder.com/300?text=No+Image"

    return src


def extract_rating(text):
    try:
        match = re.search(r"\d+(\.\d+)?", str(text))
        return float(match.group()) if match else 0.0
    except:
        return 0.0


def extract_reviews(text):
    try:
        return re.sub(r"[^\d]", "", str(text)) or "0"
    except:
        return "0"


# ==================================================
# URL CLEANERS
# ==================================================
def clean_amazon_url(url):
    url = url.strip()

    match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})",
        url
    )

    if match:
        asin = match.group(1)
        return f"https://www.amazon.in/dp/{asin}"

    return url.split("?")[0]


# ==================================================
# OPEN PAGE
# ==================================================
def open_page(url, headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=300,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
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

            window.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1,2,3,4,5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-IN', 'en-US', 'en']
            });
        """)

        page = context.new_page()

        page.goto(
            url,
            timeout=60000,
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(2000)

        for _ in range(2):
            page.mouse.wheel(0, random.randint(800, 1500))
            time.sleep(random.uniform(0.5, 1.0))

        html = page.content()

        browser.close()

        return html


def is_blocked(html):
    html = html.lower()

    blocked_words = [
        "captcha",
        "robot check",
        "enter the characters",
        "automated access",
        "sorry, we just need to make sure"
    ]

    return any(word in html for word in blocked_words)


# ==================================================
# AMAZON SCRAPER
# ==================================================
def scrape_amazon_product(url):
    try:
        url = clean_amazon_url(url)

        print("DOMAIN: www.amazon.in")
        print("Opening Amazon URL:", url)

        html = open_page(url, headless=True)

        if is_blocked(html):
            print("Amazon blocked request / CAPTCHA detected")
            return None

        soup = BeautifulSoup(html, "html.parser")

        # TITLE
        title = "N/A"

        for selector in [
            "#productTitle",
            "span#productTitle",
            "h1 span",
            "h1"
        ]:
            tag = soup.select_one(selector)

            if tag:
                title = tag.get_text(strip=True)

                if title:
                    break

        # PRICE
        price = 0

        for selector in [

            # MODERN AMAZON
            "span.a-price.aok-align-center span.a-offscreen",

            ".a-price .a-offscreen",

            "#corePrice_feature_div .a-offscreen",

            "#corePriceDisplay_desktop_feature_div .a-offscreen",

            ".priceToPay span.a-offscreen",

            ".apexPriceToPay span.a-offscreen",

            ".reinventPricePriceToPayMargin span.a-offscreen",

            "span[data-a-color='price'] span.a-offscreen",

            "span.a-price-whole",

            "#priceblock_ourprice",

            "#priceblock_dealprice"
        ]:
            tags = soup.select(selector)

            for tag in tags:
                text = (
                    tag.get("content")
                    or tag.get("aria-hidden")
                    or tag.get_text(strip=True)
                )
                price = clean_price(text)

                if price > 0:
                    break

            if price > 0:
                break

        # IMAGE
        image = "https://via.placeholder.com/300?text=No+Image"

        for selector in [
            "#landingImage",
            "#imgTagWrapperId img",
            "img.a-dynamic-image"
        ]:
            tag = soup.select_one(selector)

            if tag:
                image = clean_image(
                    tag.get("data-old-hires")
                    or tag.get("src")
                    or tag.get("data-src")
                )

                if image:
                    break

        # RATING
        rating = 0.0

        for selector in [
            "#acrPopover span.a-icon-alt",
            "span.a-icon-alt"
        ]:
            tag = soup.select_one(selector)

            if tag:
                rating = extract_rating(tag.get_text(strip=True))

                if rating > 0:
                    break

        # REVIEWS
        reviews = "0"

        for selector in [
            "#acrCustomerReviewText",
            "span[data-hook='total-review-count']"
        ]:
            tag = soup.select_one(selector)

            if tag:
                reviews = extract_reviews(tag.get_text(strip=True))

                if reviews != "0":
                    break
        
        review_url = url + "#customerReviews"
        # CUSTOMER REVIEWS
        customer_reviews = []

        review_blocks = soup.select("[data-hook='review']")

        for review in review_blocks[:5]:
            try:
                reviewer_tag = review.select_one(".a-profile-name")
                reviewer = reviewer_tag.get_text(strip=True) if reviewer_tag else "Anonymous"

                rating_tag = (
                    review.select_one("[data-hook='review-star-rating']")
                    or review.select_one("[data-hook='cmps-review-star-rating']")
                )
                review_rating = rating_tag.get_text(strip=True) if rating_tag else "No rating"

                title_tag = review.select_one("[data-hook='review-title'] span")

                review_title = (
                    title_tag.get_text(" ", strip=True)
                    if title_tag else
                    "Customer Review"
                )

                body_tag = review.select_one(
                    "[data-hook='reviewBodyContentContainer'] span"
                )

                if not body_tag:
                    body_tag = review.select_one(
                        "[data-hook='review-body'] span"
                    )

                if not body_tag:
                    body_tag = review.select_one(
                        ".review-text-content span"
                    )

                if not body_tag:
                    body_tag = review.select_one(
                        ".cr-original-review-text"
                    )

                review_body = ""

                if body_tag:

                    review_body = body_tag.get_text(
                        " ",
                        strip=True
                    )

                    review_body = review_body.replace(
                        "Read more",
                        ""
                    ).strip()

                if not review_body:
                    review_body = "No review text available"


                customer_reviews.append({
                    "reviewer": reviewer,
                    "rating": review_rating,
                    "title": review_title,
                    "body": review_body
                })

            except:
                continue
        if title == "N/A" or price <= 0:
            print("Amazon scrape failed")
            print("TITLE:", title)
            print("PRICE:", price)
            return None

        print("Amazon product scraped successfully")
        print("TITLE:", title)
        print("PRICE:", price)

        return {
            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
            "customer_reviews": customer_reviews,
            "review_url": review_url,
            "url": url,
            "website": "Amazon"
        }

    except Exception as e:
        print("Amazon error:", e)
        return None


# ==================================================
# FLIPKART
# ==================================================
def scrape_flipkart_product(url):
    try:
        print("Opening Flipkart URL:", url)

        html = open_page(url, headless=True)

        if not html:
            print("Flipkart empty HTML")
            return None

        soup = BeautifulSoup(html, "html.parser")

        # TITLE
        title = "N/A"

        title_selectors = [
            "span.VU-ZEz",
            "span.B_NuCI",
            "h1 span",
            "h1",
            "span._35KyD6",
            "meta[property='og:title']"
        ]

        for selector in title_selectors:

            tag = soup.select_one(selector)

            if not tag:
                continue

            if tag.name == "meta":
                title = tag.get("content", "").strip()
            else:
                title = tag.get_text(" ", strip=True)

            if title:
                break

        # PRICE
        price = 0

        price_selectors = [
            "div.Nx9bqj.CxhGGd",
            "div.Nx9bqj",
            "div._30jeq3._16Jk6d",
            "div._30jeq3",
            "div._16Jk6d",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']"
        ]

        for selector in price_selectors:

            tag = soup.select_one(selector)

            if not tag:
                continue

            text = (
                tag.get("content", "")
                if tag.name == "meta"
                else tag.get_text(" ", strip=True)
            )

            price = clean_price(text)

            if price > 0:
                break

        # FALLBACK PRICE SEARCH
        if price <= 0:

            page_text = soup.get_text(" ", strip=True)

            matches = re.findall(
                r"₹\s?[\d,]+",
                page_text
            )

            for m in matches:

                extracted = clean_price(m)

                if extracted > 0:
                    price = extracted
                    break

        # IMAGE
        image = "https://via.placeholder.com/300?text=No+Image"

        image_tag = (
            soup.select_one("meta[property='og:image']")
            or soup.select_one("img")
        )

        if image_tag:

            image = clean_image(
                image_tag.get("content")
                or image_tag.get("src")
                or image_tag.get("data-src")
                or ""
            )

        # RATING
        rating = 0.0

        rating_tag = (
            soup.select_one("div.XQDdHH")
            or soup.select_one("div._3LWZlK")
        )

        if rating_tag:
            rating = extract_rating(
                rating_tag.get_text(strip=True)
            )

        # REVIEWS
        reviews = "0"

        review_tag = (
            soup.select_one("span.Wphh3N")
            or soup.select_one("span._2_R_DZ")
        )

        if review_tag:
            reviews = review_tag.get_text(
                strip=True
            )

        print("TITLE:", title)
        print("PRICE:", price)

        if title == "N/A":
            return None

        if price <= 0:
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
        print("Flipkart error:", e)
        return None

# ==================================================
# SNAPDEAL
# ==================================================
def scrape_snapdeal_product(url):
    try:
        print("Opening Snapdeal URL:", url)

        html = open_page(url, headless=True)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = (
            soup.select_one("h1[itemprop='name']")
            or soup.select_one("h1.pdp-e-i-head")
            or soup.select_one("h1")
        )

        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        price_tag = (
            soup.select_one("span.payBlkBig")
            or soup.select_one("span[itemprop='price']")
            or soup.select_one(".pdp-final-price")
            or soup.select_one(".price")
        )

        price = clean_price(price_tag.get_text(strip=True) if price_tag else "")

        image_tag = (
            soup.select_one("#bx-slider-left-image-panel img")
            or soup.select_one("img.cloudzoom")
            or soup.select_one("img[itemprop='image']")
            or soup.select_one("img")
        )

        image = clean_image(
            image_tag.get("data-src")
            or image_tag.get("data-original")
            or image_tag.get("src")
        ) if image_tag else "https://via.placeholder.com/300?text=No+Image"

        rating_tag = (
            soup.select_one(".avrg-rating")
            or soup.select_one(".rating")
            or soup.select_one("[class*='rating']")
        )

        rating = extract_rating(rating_tag.get_text(strip=True)) if rating_tag else 0.0

        review_tag = (
            soup.select_one(".total-rating")
            or soup.select_one(".rating-count")
            or soup.select_one("[class*='review']")
        )

        reviews = review_tag.get_text(strip=True) if review_tag else "0"

        if title == "N/A" or price <= 0:
            print("Snapdeal scrape failed")
            return None

        return {
            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
            "url": url,
            "website": "Snapdeal"
        }

    except Exception as e:
        print("Snapdeal error:", e)
        return None


# ==================================================
# SHOPCLUES
# ==================================================
def scrape_shopclues_product(url):
    try:
        print("Opening ShopClues URL:", url)

        html = open_page(url, headless=True)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = (
            soup.select_one("h1")
            or soup.select_one(".prod_name")
            or soup.select_one("[itemprop='name']")
        )

        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        price_tag = (
            soup.select_one(".f_price")
            or soup.select_one(".p_price")
            or soup.select_one("#sec_discounted_price")
            or soup.select_one("[itemprop='price']")
            or soup.select_one(".price")
        )

        price = clean_price(price_tag.get_text(strip=True) if price_tag else "")

        image_tag = (
            soup.select_one("#zoom_picture")
            or soup.select_one(".prod_img img")
            or soup.select_one("img[itemprop='image']")
            or soup.select_one("img")
        )

        image = clean_image(
            image_tag.get("data-src")
            or image_tag.get("data-original")
            or image_tag.get("src")
        ) if image_tag else "https://via.placeholder.com/300?text=No+Image"

        rating_tag = (
            soup.select_one(".rating")
            or soup.select_one(".prod_rating")
            or soup.select_one("[class*='rating']")
        )

        rating = extract_rating(rating_tag.get_text(strip=True)) if rating_tag else 0.0

        review_tag = (
            soup.select_one(".review")
            or soup.select_one(".reviews")
            or soup.select_one("[class*='review']")
        )

        reviews = review_tag.get_text(strip=True) if review_tag else "0"

        if title == "N/A" or price <= 0:
            print("ShopClues scrape failed")
            return None

        return {
            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
            "url": url,
            "website": "ShopClues"
        }

    except Exception as e:
        print("ShopClues error:", e)
        return None


# ==================================================
# ROUTER
# ==================================================
def scrape_from_url(url):
    try:
        if not url:
            return None

        domain = urlparse(url).netloc.lower()

        print("DOMAIN:", domain)

        if "amazon" in domain:
            return scrape_amazon_product(url)

        if "flipkart" in domain:
            return scrape_flipkart_product(url)

        if "snapdeal" in domain:
            return scrape_snapdeal_product(url)

        if "shopclues" in domain:
            return scrape_shopclues_product(url)

        print("Unsupported website")
        return None

    except Exception as e:
        print("URL routing error:", e)
        return None
# ==================================================
# File: app/scrapers/url_scraper.py
# Direct Product URL Scraper
# Supports: Amazon, Flipkart, Snapdeal, ShopClues
# ==================================================

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

        text = str(text).replace("₹", "").replace(",", "").replace("Rs.", "").strip()
        match = re.search(r"\d+(\.\d+)?", text)

        return int(float(match.group())) if match else 0
    except:
        return 0


def clean_image(src):
    if not src:
        return "https://via.placeholder.com/300?text=No+Image"

    src = src.strip()

    if src.startswith("//"):
        src = "https:" + src

    if src.startswith("/"):
        return src

    if src.startswith("data:image"):
        return "https://via.placeholder.com/300?text=No+Image"

    return src


def extract_rating(text):
    try:
        if not text:
            return 0.0

        match = re.search(r"\d+(\.\d+)?", str(text))
        return float(match.group()) if match else 0.0
    except:
        return 0.0


# ==================================================
# OPEN PAGE
# ==================================================
def open_page(url, headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )

        page = context.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page.goto(url, timeout=90000, wait_until="domcontentloaded")
        time.sleep(random.uniform(5, 8))

        for _ in range(3):
            page.mouse.wheel(0, 2500)
            time.sleep(1)

        html = page.content()
        browser.close()

        return html


# ==================================================
# AMAZON
# ==================================================
def scrape_amazon_product(url):
    try:
        print("Opening Amazon URL:", url)

        html = open_page(url, headless=True)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.select_one("#productTitle")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        price = 0
        price_selectors = [
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            ".a-price-whole"
        ]

        for selector in price_selectors:
            tag = soup.select_one(selector)
            if tag:
                price = clean_price(tag.get_text(strip=True))
                if price > 0:
                    break

        image = "https://via.placeholder.com/300?text=No+Image"
        image_tag = soup.select_one("#landingImage")

        if image_tag:
            image = clean_image(
                image_tag.get("src")
                or image_tag.get("data-old-hires")
                or image
            )

        rating_tag = soup.select_one("span.a-icon-alt")
        rating = extract_rating(rating_tag.get_text(strip=True)) if rating_tag else 0.0

        review_tag = soup.select_one("#acrCustomerReviewText")
        reviews = review_tag.get_text(strip=True) if review_tag else "0"

        if title == "N/A" or price <= 0:
            print("Amazon scrape failed")
            return None

        return {
            "title": title,
            "price": price,
            "image": image,
            "rating": rating,
            "reviews": reviews,
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
        soup = BeautifulSoup(html, "html.parser")

        title_tag = (
            soup.select_one("span.VU-ZEz")
            or soup.select_one("span.B_NuCI")
            or soup.select_one("h1 span")
            or soup.select_one("h1")
        )
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        price_tag = (
            soup.select_one("div.Nx9bqj.CxhGGd")
            or soup.select_one("div.Nx9bqj")
            or soup.select_one("div._30jeq3")
            or soup.select_one("div._16Jk6d")
        )
        price = clean_price(price_tag.get_text(strip=True) if price_tag else "")

        image_tag = (
            soup.select_one("img.DByuf4")
            or soup.select_one("img._396cs4")
            or soup.select_one("img")
        )
        image = clean_image(
            image_tag.get("src") or image_tag.get("data-src")
        ) if image_tag else "https://via.placeholder.com/300?text=No+Image"

        rating_tag = (
            soup.select_one("div.XQDdHH")
            or soup.select_one("div._3LWZlK")
        )
        rating = extract_rating(rating_tag.get_text(strip=True)) if rating_tag else 0.0

        review_tag = (
            soup.select_one("span.Wphh3N")
            or soup.select_one("span._2_R_DZ")
        )
        reviews = review_tag.get_text(strip=True) if review_tag else "0"

        if title == "N/A" or price <= 0:
            print("Flipkart scrape failed")
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
# SNAPDEAL DIRECT PRODUCT PAGE
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

        image = "https://via.placeholder.com/300?text=No+Image"
        if image_tag:
            image = clean_image(
                image_tag.get("data-src")
                or image_tag.get("data-original")
                or image_tag.get("src")
                or image
            )

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
# SHOPCLUES DIRECT PRODUCT PAGE
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

        image = "https://via.placeholder.com/300?text=No+Image"
        if image_tag:
            image = clean_image(
                image_tag.get("data-src")
                or image_tag.get("data-original")
                or image_tag.get("src")
                or image
            )

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

        elif "flipkart" in domain:
            return scrape_flipkart_product(url)

        elif "snapdeal" in domain:
            return scrape_snapdeal_product(url)

        elif "shopclues" in domain:
            return scrape_shopclues_product(url)

        else:
            print("Unsupported website")
            return None

    except Exception as e:
        print("URL routing error:", e)
        return None
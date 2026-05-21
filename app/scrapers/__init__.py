"""
Scrapers Package Initialization

This module:
✔ Registers all available scrapers
✔ Provides unified interface to run them
✔ Ensures consistent output format
✔ Handles errors safely
"""

import logging

# Import all scrapers here
from .amazon import search_amazon
from .snapdeal import search_snapdeal
from .shopclues import search_shopclues
from .flipkart import search_flipkart
# ================= LOGGER =================
logger = logging.getLogger("scrapers")
logger.setLevel(logging.INFO)

# ================= SCRAPER REGISTRY =================
SCRAPERS = {
    "Amazon": search_amazon,
    "Snapdeal": search_snapdeal,
    "ShopClues": search_shopclues,
    "Flipkart": search_flipkart
}


# ================= STANDARD FORMAT =================
def normalize_product(item, site_name):
    """
    Ensures all scrapers return consistent data structure
    """

    return {
        "title": item.get("title", "").strip(),
        "price": item.get("price", 0),
        "image": item.get("image", ""),
        "url": item.get("link") or item.get("url"),
        "site": site_name,
    }


# ================= RUN SINGLE SCRAPER =================
def run_scraper(site_name, query):
    """
    Run a single scraper safely
    """

    scraper = SCRAPERS.get(site_name)

    if not scraper:
        logger.warning(f"⚠️ Scraper not found: {site_name}")
        return []

    try:
        results = scraper(query)

        normalized = [
            normalize_product(item, site_name)
            for item in results
            if item
        ]

        logger.info(f"✅ {site_name}: {len(normalized)} results")

        return normalized

    except Exception as e:
        logger.error(f"❌ {site_name} failed: {str(e)}")
        return []


# ================= RUN ALL SCRAPERS =================
def run_all_scrapers(query):
    """
    Run all scrapers sequentially
    (Threading handled in service layer if needed)
    """

    all_results = []

    for site_name in SCRAPERS:
        results = run_scraper(site_name, query)
        all_results.extend(results)

    logger.info(f"🔥 Total results: {len(all_results)}")

    return all_results


# ================= AVAILABLE SITES =================
def get_available_sites():
    """
    Return list of supported e-commerce sites
    """

    return list(SCRAPERS.keys())
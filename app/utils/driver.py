# ==========================================================
# File: utils/driver.py
# FINAL STABLE VERSION (NO webdriver-manager)
# ==========================================================

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger("driver")


def get_driver(headless=True):
    """
    Modern Selenium Driver (AUTO HANDLED)

    ✔ No webdriver-manager
    ✔ No version mismatch ever
    ✔ Works with Chrome 147+
    ✔ Uses Selenium Manager internally
    """

    try:
        options = Options()

        # ==========================================
        # HEADLESS
        # ==========================================
        if headless:
            options.add_argument("--headless=new")

        # ==========================================
        # PERFORMANCE
        # ==========================================
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        # ==========================================
        # ANTI-BOT
        # ==========================================
        options.add_argument("--disable-blink-features=AutomationControlled")

        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36"
        )

        # ==========================================
        # 🚀 KEY FIX: NO DRIVER MANAGER
        # ==========================================
        driver = webdriver.Chrome(options=options)

        # ==========================================
        # STEALTH FIX
        # ==========================================
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("✅ ChromeDriver initialized (Selenium Manager)")

        return driver

    except Exception as e:
        logger.error(f"❌ Driver initialization failed: {str(e)}")
        return None
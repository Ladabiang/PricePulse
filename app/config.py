"""
config.py
--------------------------------------
PROFESSIONAL Production-Ready Config
PricePulse 2026 Edition

Features:
✔ Development / Production / Testing
✔ Secure Secret Keys
✔ Gmail SMTP Ready
✔ Forgot Password Ready
✔ Session Security
✔ Flask SQLAlchemy Ready
✔ Scheduler Ready
✔ Logging Ready
✔ Scraper Ready
✔ Environment Variable Support
"""

import os
from datetime import timedelta


# ======================================================
# BASE CONFIG
# ======================================================
class Config:

    # ==================================================
    # CORE SECURITY
    # ==================================================
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "pricepulse_super_secret_key_change_me_2026"
    )

    WTF_CSRF_ENABLED = True

    # ==================================================
    # DATABASE (POSTGRESQL ONLY)
    # ==================================================

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:Post@localhost:5432/pricepulse"
    )

    if DATABASE_URL.startswith("postgres://"):

        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==================================================
    # SESSION SECURITY
    # ==================================================
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # ==================================================
    # MAIL CONFIGURATION (GMAIL SMTP)
    # ==================================================
    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    MAIL_PORT = int(
        os.getenv("MAIL_PORT", 587)
    )

    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        "lyngkhoiladabiang04@gmail.com"
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD",
        "qvfelnxffcdcxnmj"
    )

    # What user sees in inbox
    MAIL_DEFAULT_SENDER = (
        "PricePulse Security Team",
        MAIL_USERNAME
    )

    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    # ==================================================
    # PASSWORD RESET
    # ==================================================
    RESET_TOKEN_EXPIRES = 900   # 15 min

    # ==================================================
    # APP FEATURES
    # ==================================================
    ITEMS_PER_PAGE = 20

    TRACKER_INTERVAL_MINUTES = 30
    ENABLE_SCHEDULER = True

    # ==================================================
    # SCRAPER SETTINGS
    # ==================================================
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )

    # ==================================================
    # LOGGING
    # ==================================================
    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    # ==================================================
    # MISC
    # ==================================================
    JSON_SORT_KEYS = False


# ======================================================
# DEVELOPMENT CONFIG
# ======================================================
class DevelopmentConfig(Config):

    DEBUG = True
    ENV = "development"


# ======================================================
# PRODUCTION CONFIG
# ======================================================
class ProductionConfig(Config):

    DEBUG = False
    ENV = "production"

    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI


# ======================================================
# TESTING CONFIG
# ======================================================
class TestingConfig(Config):

    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# ======================================================
# CONFIG MAP
# ======================================================
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
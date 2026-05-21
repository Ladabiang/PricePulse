import os
from datetime import timedelta


class Config:
    # ==================================================
    # CORE SECURITY
    # ==================================================
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "pricepulse_dev_secret_key_change_later"
    )

    WTF_CSRF_ENABLED = True

    # ==================================================
    # DATABASE
    # ==================================================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///database.db"
    )

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
    # GMAIL SMTP CONFIG
    # ==================================================
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = (
        "PricePulse Smart Tracker",
        MAIL_USERNAME
    )

    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    # ==================================================
    # PASSWORD RESET
    # ==================================================
    RESET_TOKEN_EXPIRES = 900

    # ==================================================
    # APP FEATURES
    # ==================================================
    ITEMS_PER_PAGE = 20
    TRACKER_INTERVAL_MINUTES = int(os.getenv("TRACKER_INTERVAL_MINUTES", 30))
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

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
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"

    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///database.db"
    )


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
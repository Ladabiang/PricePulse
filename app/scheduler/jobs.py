import logging
import re
from datetime import datetime

from utils.email_alert import send_price_alert
from models import (
    db,
    Product,
    ProductLink,
    PriceHistory,
    TrackedProduct,
    User
)

from services.scraper_service import search_all_sites
from log_activity import add_log

# ================= LOGGER =================
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)


# ================= HELPER =================
def clean_price(price_text):
    clean = re.sub(r"[^\d]", "", str(price_text))
    return int(clean) if clean else 0


# ================= MAIN JOB =================
def run_price_check():

    logger.info("Starting scheduled price check...")

    try:
        tracked_products = TrackedProduct.query.filter_by(is_active=True).all()

        if not tracked_products:
            logger.info("No tracked products found.")
            return

        for tracked in tracked_products:

            product = Product.query.get(tracked.product_id)

            if not product:
                continue

            logger.info(f"Checking: {product.title}")

            try:
                # ==================================
                # SCRAPE LATEST PRICES
                # ==================================
                results = search_all_sites(product.title)

                if not results:
                    logger.warning(f"No results for {product.title}")
                    continue

                prices = []

                for item in results:
                    price_clean = clean_price(item.get("price"))

                    if price_clean > 0:
                        prices.append(price_clean)

                if not prices:
                    logger.warning(f"No valid prices for {product.title}")
                    continue

                current_price = min(prices)

                # ==================================
                # GET LAST SAVED PRICE
                # ==================================
                last_entry = (
                    PriceHistory.query
                    .join(ProductLink)
                    .filter(ProductLink.product_id == product.id)
                    .order_by(PriceHistory.checked_at.desc())
                    .first()
                )

                last_price = last_entry.price if last_entry else None

                # ==================================
                # GET PRODUCT LINK
                # ==================================
                link = ProductLink.query.filter_by(
                    product_id=product.id
                ).first()

                if not link:
                    logger.warning(f"No link for product {product.id}")
                    continue

                # ==================================
                # SAVE HISTORY
                # ==================================
                history = PriceHistory(
                    link_id=link.id,
                    price=current_price,
                    checked_at=datetime.utcnow()
                )

                db.session.add(history)

                tracked.price = current_price
                tracked.last_checked = datetime.utcnow()

                # ==================================
                # ALERT LOGIC
                # ==================================
                alert_triggered = False

                if tracked.target_price and current_price <= tracked.target_price:
                    alert_triggered = True
                    logger.info(f"Target reached for {product.title}")

                if last_price and current_price < last_price:
                    drop_percent = (
                        (last_price - current_price) / last_price
                    ) * 100

                    if drop_percent >= 5:
                        alert_triggered = True
                        logger.info(
                            f"Dropped {drop_percent:.2f}% for {product.title}"
                        )

                db.session.commit()

                add_log(
                    f"Auto price checked: {product.title}",
                    "System"
                )

                # ==================================
                # SEND ALERT
                # ==================================
                if alert_triggered:
                    trigger_notification(tracked, product, current_price)

            except Exception as e:
                db.session.rollback()

                logger.error(
                    f"Error processing {product.title}: {str(e)}"
                )

                add_log(
                    f"Scheduler failed for {product.title}",
                    "System"
                )

        logger.info("Price check completed")
        add_log("Auto price scraper completed", "System")

    except Exception as e:
        logger.critical(f"Scheduler failed: {str(e)}")
        add_log("Scheduler critical failure", "System")


# ================= NOTIFICATION =================
def trigger_notification(tracked, product, price):

    logger.info(f"""
🔔 ALERT TRIGGERED
Product: {product.title}
Price: ₹{price}
Time: {datetime.utcnow()}
""")

    add_log(
        f"Price alert sent for {product.title}",
        "System"
    )

    try:
        from flask_mail import Message
        from app import mail

        user = User.query.get(tracked.user_id)

        if not user:
            return

        msg = Message(
            subject="Price Drop Alert",
            recipients=[user.email]
        )

        msg.body = f"""
Hello {user.username},

Good news!

{product.title}

Current Price: ₹{price}
Target Price: ₹{tracked.target_price}

Buy now:
{tracked.product_url}

- PricePulse
"""

        mail.send(msg)

        logger.info("Email sent")
        add_log(
            f"Email alert sent to {user.username}",
            "System"
        )

    except Exception as e:
        logger.warning(f"Email not sent: {str(e)}")
        add_log("Email sending failed", "System")


# ================= MANUAL RUN =================
def manual_run():
    logger.info("Manual trigger started")
    add_log("Manual scheduler trigger", "Admin")
    run_price_check()
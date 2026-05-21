# ==================================================
# File: app/services/price_updater.py
# Background Price Tracker + Email Alert
# ==================================================

from datetime import datetime, timezone

from app.extensions import db

from app.models.tracked_product import TrackedProduct
from app.models.product import Product
from app.models.product_link import ProductLink
from app.models.price_history import PriceHistory
from app.models.user import User

from app.scrapers.url_scraper import scrape_from_url
from app.services.email_service import send_price_drop_email


# ==================================================
# UPDATE ALL TRACKED PRODUCT PRICES
# ==================================================
def update_all_prices():

    print("\n========== PRICE CHECK STARTED ==========\n")

    tracked_items = TrackedProduct.query.filter_by(
        is_active=True
    ).all()

    if not tracked_items:
        print("No active tracked products found.")
        print("\n========== PRICE CHECK FINISHED ==========\n")
        return

    for item in tracked_items:

        try:
            print(f"Checking: {item.product_name}")

            if not item.product_url:
                print("No product URL found. Skipping.")
                continue

            # ================= SCRAPE LATEST PRICE =================
            scraped_product = scrape_from_url(item.product_url)

            if not scraped_product:
                print("Failed scraping.")
                continue

            new_price = float(scraped_product.get("price", 0) or 0)
            old_price = float(item.price or 0)

            print("OLD PRICE:", old_price)
            print("NEW PRICE:", new_price)

            if new_price <= 0:
                print("Invalid price. Skipping.")
                continue

            # ================= FIND PRODUCT =================
            product = db.session.get(Product, item.product_id)

            if product:
                product.price = new_price
                product.old_price = old_price
                product.updated_at = datetime.now(timezone.utc)

                if scraped_product.get("image"):
                    product.image = scraped_product.get("image")

                if scraped_product.get("rating") is not None:
                    try:
                        product.rating = float(scraped_product.get("rating") or 0)
                    except:
                        product.rating = 0

                if scraped_product.get("reviews") is not None:
                    product.reviews = str(scraped_product.get("reviews"))

            # ================= UPDATE TRACKED PRODUCT =================
            item.old_price = old_price
            item.price = new_price
            item.last_checked = datetime.now(timezone.utc)
            item.updated_at = datetime.now(timezone.utc)

            # Reset alert if price goes above target again
            if item.target_price and new_price > item.target_price:
                item.alert_sent = False

            # ================= FIND PRODUCT LINK =================
            link = ProductLink.query.filter_by(
                product_id=item.product_id
            ).first()

            if link:
                link.current_price = new_price

                if scraped_product.get("url"):
                    link.url = scraped_product.get("url")

            else:
                link = ProductLink(
                    product_id=item.product_id,
                    website=item.website or scraped_product.get("website", "Unknown"),
                    url=item.product_url,
                    current_price=new_price
                )

                db.session.add(link)
                db.session.flush()

            # ================= CALCULATE PRICE CHANGE =================
            price_change = round(old_price - new_price, 2) if old_price else 0

            change_percent = 0

            if old_price and old_price > 0:
                change_percent = round(
                    ((old_price - new_price) / old_price) * 100,
                    2
                )

            # ================= SAVE PRICE HISTORY =================
            history = PriceHistory(
                link_id=link.id,
                product_id=item.product_id,
                old_price=old_price,
                price=new_price,
                price_change=price_change,
                change_percent=change_percent,
                website=item.website or scraped_product.get("website", "Unknown"),
                checked_at=datetime.now(timezone.utc)
            )

            db.session.add(history)

            # ==================================================
            # EMAIL ALERT CONDITIONS
            # ==================================================
            should_send_email = False

            # Case 1: price decreased compared to old price
            if old_price > 0 and new_price < old_price:
                should_send_email = True
                print("PRICE DROP DETECTED!")

            # Case 2: target price reached
            if item.target_price and new_price <= item.target_price:
                should_send_email = True
                print("TARGET PRICE REACHED!")

            # Prevent repeated target emails
            if should_send_email and not item.alert_sent:

                user = db.session.get(User, item.user_id)

                if user:
                    send_price_drop_email(
                        user.email,
                        item.product_name,
                        old_price,
                        new_price,
                        item.product_url
                    )

                    item.alert_sent = True
                    item.last_alert_sent = datetime.now(timezone.utc)

                    print("EMAIL SENT TO:", user.email)

            db.session.commit()

            print("Updated successfully.\n")

        except Exception as e:
            db.session.rollback()
            print("UPDATE ERROR:", e)

    print("\n========== PRICE CHECK FINISHED ==========\n")
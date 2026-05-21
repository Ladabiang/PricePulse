# ==================================================
# app/scheduler.py
# FINAL FIXED VERSION
# ==================================================

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


# ==================================================
# START SCHEDULER
# ==================================================
def start_scheduler(app):

    # prevent duplicate scheduler
    if not scheduler.running:

        # ==================================================
        # WRAPPER FUNCTION
        # THIS FIXES APP CONTEXT ERROR
        # ==================================================
        def scheduled_price_update():

            with app.app_context():

                from app.services.price_updater import (
                    update_all_prices
                )

                update_all_prices()

        # ==================================================
        # ADD JOB
        # ==================================================
        scheduler.add_job(
            func=scheduled_price_update,

            trigger="interval",

            minutes=30,   # testing mode

            id="price_tracker_job",

            replace_existing=True
        )

        scheduler.start()

        print("Background price tracker started")
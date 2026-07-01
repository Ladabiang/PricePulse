from apscheduler.schedulers.background import BackgroundScheduler

# ==================================================
# CREATE GLOBAL SCHEDULER
# ==================================================
scheduler = BackgroundScheduler()


# ==================================================
# START SCHEDULER
# ==================================================
def start_scheduler(app):

    # ==============================================
    # PREVENT DUPLICATE SCHEDULERS
    # ==============================================
    if scheduler.running:

        print("Scheduler already running")

        return

    # ==============================================
    # MAIN BACKGROUND TASK
    # ==============================================
    def scheduled_price_update():

        print("\n===================================")
        print("SCHEDULER RUNNING NOW")
        print("Checking tracked products...")
        print("===================================\n")

        try:

            with app.app_context():

                from app.services.price_updater import (
                    update_all_prices
                )

                update_all_prices()

            print("\n===================================")
            print("SCHEDULER FINISHED SUCCESSFULLY")
            print("===================================\n")

        except Exception as e:

            print("\n===================================")
            print(f"SCHEDULER ERROR: {e}")
            print("===================================\n")

    # ==============================================
    # ADD BACKGROUND JOB
    # ==============================================
    scheduler.add_job(

        func=scheduled_price_update,

        trigger="interval",

        # ==========================================
        # TEST MODE
        # CHANGE TO 30 LATER
        # ==========================================
        minutes=30,

        id="price_tracker_job",

        replace_existing=True

    )

    # ==============================================
    # START SCHEDULER
    # ==============================================
    scheduler.start()

    print("\n===================================")
    print("BACKGROUND PRICE TRACKER STARTED")
    print("Scheduler interval: 30 minute")
    print("===================================\n")
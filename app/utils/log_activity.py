# ==========================================================
# File: app/utils/log_activity.py
# Production Ready Activity Logger
# ==========================================================

from flask import request, has_request_context
from flask_login import current_user
from datetime import datetime, timezone
import logging

# FIXED IMPORTS
from app.extensions import db
from app.models.activity_log import ActivityLog


# ==========================================================
# LOGGER CONFIG
# ==========================================================

logger = logging.getLogger("activity_logger")
logger.setLevel(logging.INFO)


# ==========================================================
# SAFE ATTRIBUTE SETTER
# ==========================================================

def safe_set(obj, field, value):
    if hasattr(obj, field):
        setattr(obj, field, value)


# ==========================================================
# MAIN FUNCTION (THIS IS WHAT ROUTES IMPORT)
# ==========================================================

def log_activity(action, username=None):
    """
    Universal activity logger
    Use anywhere in project:
    log_activity("User Logged In")
    """

    try:
        # ----------------------------
        # Detect username
        # ----------------------------
        if username is None:
            if has_request_context() and current_user.is_authenticated:
                username = current_user.username
            else:
                username = "System"

        # ----------------------------
        # Detect IP
        # ----------------------------
        if has_request_context():
            ip_address = request.remote_addr or "Unknown"
        else:
            ip_address = "System"

        # ----------------------------
        # Create log row
        # ----------------------------
        log = ActivityLog()

        safe_set(log, "action", action)
        safe_set(log, "username", username)
        safe_set(log, "ip_address", ip_address)
        safe_set(log, "created_at", datetime.now(timezone.utc))

        db.session.add(log)
        db.session.commit()

        logger.info(f"[LOG SAVED] {username} | {action}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"[LOG ERROR] {str(e)}")


# ==========================================================
# BULK LOGGING
# ==========================================================

def add_bulk_logs(log_list):

    try:
        logs = []

        for item in log_list:
            log = ActivityLog()

            safe_set(log, "action", item.get("action"))
            safe_set(log, "username", item.get("username", "System"))
            safe_set(log, "ip_address", "System")
            safe_set(log, "created_at", datetime.now(timezone.utc))

            logs.append(log)

        db.session.bulk_save_objects(logs)
        db.session.commit()

        logger.info(f"[BULK LOG] {len(logs)} logs inserted")

    except Exception as e:
        db.session.rollback()
        logger.error(f"[BULK LOG ERROR] {str(e)}")
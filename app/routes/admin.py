# ==================================================
# app/routes/admin.py
# FINAL CLEAN + SAFE VERSION + ACTIVITY LOGGING
# ==================================================

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    Response,
    request
)

from flask_login import login_required, current_user
import csv
import io

from app.extensions import db

# ==================================================
# MODELS
# ==================================================
from app.models.user import User
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.tracked_product import TrackedProduct
from app.models.alert import Alert

# ==================================================
# UTILITIES
# ==================================================
from app.utils.log_activity import log_activity

# ==================================================
# BLUEPRINT
# ==================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ==================================================
# ADMIN CHECK
# ==================================================
def is_admin():
    return (
        current_user.is_authenticated and
        hasattr(current_user, "role") and
        current_user.role == "admin"
    )


def admin_required():
    if not is_admin():
        flash("Access denied. Admin only.", "danger")
        return False
    return True


# ==================================================
# SAFE COUNT
# ==================================================
def safe_count(model):
    return db.session.query(model).count()


# ==================================================
# DASHBOARD
# ==================================================
@admin_bp.route("/")
@login_required
def admin_dashboard():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    prices = db.session.query(PriceHistory.price).limit(100).all()
    prices = [float(p[0]) for p in prices] if prices else [0]

    logs = []

    try:
        from app.models.activity_log import ActivityLog
        logs = ActivityLog.query.order_by(
            ActivityLog.created_at.desc()
        ).limit(10).all()
    except:
        logs = []

    return render_template(
        "admin/dashboard.html",
        total_users=safe_count(User),
        total_products=safe_count(Product),
        total_tracking=safe_count(TrackedProduct),
        lowest_price=min(prices),
        highest_price=max(prices),
        chart_labels=[f"#{i+1}" for i in range(len(prices))],
        chart_prices=prices,
        logs=logs
    )


# ==================================================
# USERS
# ==================================================
@admin_bp.route("/users")
@login_required
def users():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    page = request.args.get("page", 1, type=int)

    users = User.query.order_by(User.id.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template("admin/users.html", users=users)


# ==================================================
# PRODUCTS
# ==================================================
@admin_bp.route("/products")
@login_required
def products():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    page = request.args.get("page", 1, type=int)

    products = Product.query.order_by(Product.id.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template("admin/products.html", products=products)


# ==================================================
# PRICE HISTORY
# ==================================================
@admin_bp.route("/price-history")
@login_required
def price_history():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    page = request.args.get("page", 1, type=int)

    history = PriceHistory.query.order_by(
        PriceHistory.checked_at.desc()
    ).paginate(
        page=page,
        per_page=15,
        error_out=False
    )

    return render_template("admin/price_history.html", history=history)


# ==================================================
# ALERTS
# ==================================================
@admin_bp.route("/alerts")
@login_required
def alerts():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    page = request.args.get("page", 1, type=int)

    alert_data = Alert.query.order_by(Alert.id.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template("admin/alerts.html", alerts=alert_data)


# ==================================================
# WATCHLIST
# ==================================================
@admin_bp.route("/watchlist")
@login_required
def watchlist():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    page = request.args.get("page", 1, type=int)

    watchlist = TrackedProduct.query.order_by(
        TrackedProduct.id.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template("admin/watchlist.html", watchlist=watchlist)


# ==================================================
# REPORTS
# ==================================================
@admin_bp.route("/reports")
@login_required
def reports():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    log_activity("Viewed Reports")

    return render_template(
        "admin/reports.html",
        total_users=safe_count(User),
        total_products=safe_count(Product),
        total_tracking=safe_count(TrackedProduct)
    )


# ==================================================
# TOGGLE BAN USER
# ==================================================
@admin_bp.route("/toggle-ban/<int:user_id>")
@login_required
def toggle_ban(user_id):

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))

    if user.id == current_user.id:
        flash("You cannot ban yourself.", "warning")
        return redirect(url_for("admin.users"))

    if user.role == "admin":
        flash("Admin cannot be banned.", "warning")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    db.session.commit()

    if user.is_active:
        flash("User unbanned successfully.", "success")
        log_activity(f"Unbanned user {user.username}")
    else:
        flash("User banned successfully.", "success")
        log_activity(f"Banned user {user.username}")

    return redirect(url_for("admin.users"))


# ==================================================
# DELETE USER
# ==================================================
@admin_bp.route("/delete-user/<int:user_id>")
@login_required
def delete_user(user_id):

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))

    if user.id == current_user.id:
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for("admin.users"))

    if user.role == "admin":
        flash("Admin cannot be deleted.", "warning")
        return redirect(url_for("admin.users"))

    username = user.username

    db.session.delete(user)
    db.session.commit()

    log_activity(f"Deleted user {username}")

    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.users"))


# ==================================================
# DELETE PRODUCT
# ==================================================
@admin_bp.route("/delete-product/<int:product_id>")
@login_required
def delete_product(product_id):

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    product = db.session.get(Product, product_id)

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin.products"))

    title = product.title

    db.session.delete(product)
    db.session.commit()

    log_activity(f"Deleted product {title}")

    flash("Product deleted successfully.", "success")
    return redirect(url_for("admin.products"))


# ==================================================
# EXPORT USERS
# ==================================================
@admin_bp.route("/export-users")
@login_required
def export_users():

    if not admin_required():
        return redirect(url_for("web.dashboard"))

    users = User.query.order_by(User.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Username", "Email", "Role", "Status"])

    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.role,
            "Active" if user.is_active else "Banned"
        ])

    output.seek(0)

    log_activity("Exported Users CSV")

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=users_export.csv"
        }
    )
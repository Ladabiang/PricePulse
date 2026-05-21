# ==================================================
# app/routes/auth.py
# FINAL PROFESSIONAL VERSION WITH ACTIVITY LOGGING
# ==================================================

from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    render_template,
    current_app
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

from app.extensions import db, bcrypt, mail
from app.models.user import User
from app.utils.log_activity import log_activity

# ==================================================
# BLUEPRINT
# ==================================================
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ==================================================
# LOGIN
# ==================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # If already logged in
    if current_user.is_authenticated:

        if getattr(current_user, "role", "user") == "admin":
            return redirect(url_for("admin.admin_dashboard"))

        return redirect(url_for("web.dashboard"))

    # Show page
    if request.method == "GET":
        return render_template("auth/login.html")

    # Receive form/json
    data = request.get_json() if request.is_json else request.form

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    # Validate
    if not email or not password:
        flash("Email and password required.", "warning")
        return redirect(url_for("auth.login"))

    user = db.session.query(User).filter_by(email=email).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if hasattr(user, "is_active") and not user.is_active:
        flash("Your account has been banned.", "danger")
        return redirect(url_for("auth.login"))

    if not bcrypt.check_password_hash(user.password, password):
        flash("Wrong password.", "danger")
        return redirect(url_for("auth.login"))

    # Login
    login_user(user)

    # Activity Log
    log_activity("User Logged In")

    flash(f"Welcome back, {user.username}!", "success")

    # Redirect by role
    if getattr(user, "role", "user") == "admin":
        return redirect(url_for("admin.admin_dashboard"))

    return redirect(url_for("web.dashboard"))


# ==================================================
# REGISTER
# ==================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("auth/register.html")

    data = request.get_json() if request.is_json else request.form

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not username or not email or not password:
        flash("All fields are required.", "warning")
        return redirect(url_for("auth.register"))

    # Duplicate checks
    if db.session.query(User).filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("auth.register"))

    if db.session.query(User).filter_by(username=username).first():
        flash("Username already taken.", "danger")
        return redirect(url_for("auth.register"))

    # First user becomes admin
    role = "admin" if db.session.query(User).count() == 0 else "user"

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    user = User(
        username=username,
        email=email,
        password=hashed_password,
        role=role
    )

    db.session.add(user)
    db.session.commit()

    # Log
    log_activity(f"New user registered: {username}")

    flash("Registration successful! Please login.", "success")
    return redirect(url_for("auth.login"))


# ==================================================
# LOGOUT
# ==================================================
@auth_bp.route("/logout")
@login_required
def logout():

    username = current_user.username

    log_activity("User Logged Out")

    logout_user()

    flash(f"{username} logged out successfully.", "success")
    return redirect(url_for("auth.login"))


# ==================================================
# FORGOT PASSWORD PAGE
# ==================================================
@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("auth/forgot_password.html")


# ==================================================
# SEND RESET LINK
# ==================================================
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json() if request.is_json else request.form
    email = data.get("email", "").strip()

    if not email:
        flash("Email required.", "warning")
        return redirect(url_for("auth.forgot_password_page"))

    user = db.session.query(User).filter_by(email=email).first()

    if not user:
        flash("Email not found.", "danger")
        return redirect(url_for("auth.forgot_password_page"))

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    token = serializer.dumps(email, salt="password-reset")

    reset_link = url_for(
        "auth.reset_password",
        token=token,
        _external=True
    )

    try:
        msg = Message(
            subject="Reset Your PricePulse Password",
            recipients=[email]
        )

        msg.html = f"""
        <h2>Password Reset Request</h2>

        <p>Hello {user.username},</p>

        <p>We received a request to reset your password.</p>

        <p>
            <a href="{reset_link}"
               style="background:#2563eb;color:white;
               padding:12px 18px;text-decoration:none;
               border-radius:8px;">
               Reset Password
            </a>
        </p>

        <p>This link expires in 15 minutes.</p>

        <p>If this wasn't you, ignore this email.</p>

        <br>
        <p>PricePulse Security Team</p>
        """

        mail.send(msg)

        log_activity(f"Password reset requested: {user.username}")

        flash("Reset link sent to your email.", "success")

    except Exception as e:
        print("MAIL ERROR:", e)
        flash("Could not send email. Check settings.", "danger")

    return redirect(url_for("auth.login"))


# ==================================================
# RESET PASSWORD
# ==================================================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=900
        )

    except Exception:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("auth/reset_password.html", token=token)

    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not password or not confirm_password:
        flash("All fields required.", "warning")
        return redirect(request.url)

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(request.url)

    user = db.session.query(User).filter_by(email=email).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    user.password = bcrypt.generate_password_hash(password).decode("utf-8")

    db.session.commit()

    log_activity(f"Password reset completed: {user.username}")

    flash("Password reset successful! Please login.", "success")
    return redirect(url_for("auth.login"))


# ==================================================
# CURRENT USER API
# ==================================================
@auth_bp.route("/me")
@login_required
def me():

    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": getattr(current_user, "role", "user")
    })
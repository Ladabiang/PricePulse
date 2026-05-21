from app.models.user import User
from app.extensions import db, bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


# =========================
# LOGIN SERVICE
# =========================
def login_user_service(email, password):
    """
    Validate user login credentials
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "User not found"

    if hasattr(user, "is_active") and not user.is_active:
        return None, "Account banned"

    if not bcrypt.check_password_hash(user.password, password):
        return None, "Wrong password"

    return user, None


# =========================
# REGISTER SERVICE
# =========================
def register_user_service(username, email, password):
    """
    Register a new user
    """

    if not username or not email or not password:
        return None, "All fields are required"

    if User.query.filter_by(email=email).first():
        return None, "Email already exists"

    if User.query.filter_by(username=username).first():
        return None, "Username already taken"

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # First user becomes admin
    role = "admin" if User.query.count() == 0 else "user"

    user = User(
        username=username,
        email=email,
        password=hashed_password,
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return user, None


# =========================
# GENERATE RESET TOKEN
# =========================
def generate_reset_token(email):
    """
    Generate password reset token
    """
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps(email, salt="password-reset")
    return token


# =========================
# VERIFY RESET TOKEN
# =========================
def verify_reset_token(token, max_age=900):
    """
    Verify token and return email
    """
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:
        email = serializer.loads(token, salt="password-reset", max_age=max_age)
        return email, None
    except Exception:
        return None, "Invalid or expired token"


# =========================
# RESET PASSWORD
# =========================
def reset_password_service(token, new_password):
    """
    Reset user password using token
    """

    email, error = verify_reset_token(token)

    if error:
        return None, error

    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "User not found"

    if not new_password:
        return None, "Password cannot be empty"

    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

    user.password = hashed_password
    db.session.commit()

    return user, None
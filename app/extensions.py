from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail

# =========================
# EXTENSIONS INSTANCES
# =========================
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()


# =========================
# LOGIN MANAGER CONFIG
# =========================
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    from app.extensions import db
    from app.models.user import User

    return db.session.get(User, int(user_id))
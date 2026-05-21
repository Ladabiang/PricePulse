from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail

from config import DevelopmentConfig
from models import db, User

# Blueprints
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.api import api_bp

# =========================================
# APP SETUP
# =========================================
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# =========================================
# EXTENSIONS
# =========================================
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login_page"  # important!

mail = Mail(app)

# =========================================
# USER LOADER
# =========================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================================
# REGISTER BLUEPRINTS
# =========================================
app.register_blueprint(auth_bp)      # /login, /register
app.register_blueprint(user_bp)      # /user/...
app.register_blueprint(admin_bp)     # /admin/...
app.register_blueprint(api_bp)       # /api/...


# =========================================
# HOME ROUTE
# =========================================
@app.route("/")
def home():
    return render_template("index.html")


# =========================================
# RUN APP
# =========================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
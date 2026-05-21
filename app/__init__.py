from flask import Flask
from app.config import Config
from flask_migrate import Migrate


# import all extensions
from app.extensions import db, bcrypt, login_manager, mail
from app.scheduler import start_scheduler


def create_app():
    print("create_app() is running...")

    app = Flask(__name__)
    app.config.from_object(Config)

    # ===================================
    # INITIALIZE EXTENSIONS
    # ===================================
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    mail.init_app(app)


    # ===================================
    # REGISTER BLUEPRINT ROUTES
    # ===================================
    from app.routes import register_routes
    register_routes(app)

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # ===================================
    # CREATE DATABASE TABLES
    # ===================================
    with app.app_context():

        from app.models.user import User
        from app.models.product import Product

        db.create_all()


    # ===================================
    # START BACKGROUND SCHEDULER
    # ===================================
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler(app)

    print("App created successfully")

    return app
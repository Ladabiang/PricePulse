from .auth import auth_bp
from .user import user_bp
from .admin import admin_bp
from .api import api_bp
from .web import web


def register_routes(app):
    app.register_blueprint(web)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

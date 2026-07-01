from app.extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email_alerts = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=False)
    weekly_reports = db.Column(db.Boolean, default=True)

    role = db.Column(db.String(20), default="user")
    is_active = db.Column(db.Boolean, default=True)

    products = db.relationship("Product", backref="user", lazy=True)
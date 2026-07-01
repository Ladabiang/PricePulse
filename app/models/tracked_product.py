from datetime import datetime, timezone
from app.extensions import db


class TrackedProduct(db.Model):
    __tablename__ = "tracked_products"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="unique_user_product"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    product_name = db.Column(db.String(300), nullable=False)
    image = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(100), nullable=False)

    price = db.Column(db.Float, default=0)
    old_price = db.Column(db.Float, nullable=True)
    target_price = db.Column(db.Float, default=0)

    product_url = db.Column(db.String(1000), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    alert_sent = db.Column(db.Boolean, default=False)
    last_alert_sent = db.Column(db.DateTime, nullable=True)

    last_checked = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        backref=db.backref("tracked_products", lazy=True)
    )
    product = db.relationship(
        "Product"
    )

    def mark_active(self):
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def mark_stopped(self):
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_price(self, new_price):
        self.old_price = self.price
        self.price = float(new_price)
        self.last_checked = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def should_send_alert(self):
        if not self.target_price:
            return False

        if not self.price:
            return False

        if self.alert_sent:
            return False

        return self.price <= self.target_price

    def __repr__(self):
        return f"<TrackedProduct {self.product_name}>"
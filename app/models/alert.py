from datetime import datetime, timezone
from app.extensions import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)

    # ================= USER =================
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # ================= PRODUCT =================
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    # ================= NOTIFICATION =================
    email = db.Column(db.String(150), nullable=False)

    # ================= TARGET =================
    target_price = db.Column(db.Float, nullable=False)

    # ================= LIVE DATA =================
    current_price = db.Column(db.Float, nullable=True)

    # ================= STATUS =================
    is_active = db.Column(db.Boolean, default=True, index=True)

    status = db.Column(
        db.String(20),
        default="pending"
    )
    # pending | triggered | disabled

    triggered_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # ================= RELATIONSHIPS =================
    user = db.relationship("User", backref="alerts")
    product = db.relationship("Product", backref="alerts")

    def check_trigger(self, current_price):
        """
        Checks if alert should be triggered based on current price.
        Call this whenever price updates.
        """

        # update snapshot
        self.current_price = current_price

        # only trigger if active and not already triggered
        if self.is_active and self.status == "pending":
            if current_price <= self.target_price:
                self.status = "triggered"
                self.triggered_at = datetime.now(timezone.utc)

        return self.status

    # ================= DEBUG =================
    def __repr__(self):
        return f"<Alert user={self.user_id} product={self.product_id} target={self.target_price}>"
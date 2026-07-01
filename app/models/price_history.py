from datetime import datetime, timezone
from app.extensions import db


class PriceHistory(db.Model):

    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)

    link_id = db.Column(
        db.Integer,
        db.ForeignKey("product_links.id"),
        nullable=False,
        index=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=True,
        index=True
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    old_price = db.Column(
        db.Float,
        nullable=True
    )

    price_change = db.Column(
        db.Float,
        default=0
    )

    change_percent = db.Column(
        db.Float,
        default=0
    )

    website = db.Column(
        db.String(100),
        nullable=True
    )

    checked_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    link = db.relationship(
        "ProductLink",
        backref=db.backref(
            "price_histories",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    product = db.relationship(
        "Product",
        backref=db.backref(
            "price_history",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def calculate_change(self):

        if self.old_price and self.old_price > 0:

            self.price_change = round(
                self.old_price - self.price,
                2
            )

            self.change_percent = round(
                ((self.old_price - self.price) / self.old_price) * 100,
                2
            )

        else:
            self.price_change = 0
            self.change_percent = 0

    def __repr__(self):
        return f"<PriceHistory ₹{self.price}>"
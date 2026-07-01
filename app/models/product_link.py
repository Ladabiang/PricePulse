from datetime import datetime, timezone
from app.extensions import db


class ProductLink(db.Model):

    __tablename__ = "product_links"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==================================================
    # PRODUCT RELATION
    # ==================================================
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    # ==================================================
    # WEBSITE INFO
    # ==================================================
    website = db.Column(
        db.String(100),
        nullable=False
    )

    url = db.Column(
        db.Text,
        nullable=False
    )

    current_price = db.Column(
        db.Float,
        default=0
    )

    is_available = db.Column(
        db.Boolean,
        default=True
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

    # ==================================================
    # PRICE HISTORY RELATIONSHIP
    # ==================================================
    price_history = db.relationship(
        "PriceHistory",

        # CHANGED FROM "link"
        backref="price_link_ref",

        cascade="all, delete-orphan",

        lazy=True
    )

    def __repr__(self):
        return f"<ProductLink {self.website}>"
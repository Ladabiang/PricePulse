from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title = db.Column(db.String(500), nullable=False)

    price = db.Column(db.Float, default=0)

    old_price = db.Column(db.Float, nullable=True)

    image = db.Column(db.Text)

    rating = db.Column(db.Float, default=0)

    reviews = db.Column(db.String(100))

    url = db.Column(db.Text)

    website = db.Column(db.String(100))

    source = db.Column(db.String(100))

    category = db.Column(
        db.String(100),
        default="General"
    )

    subcategory = db.Column(
        db.String(100),
        nullable=True
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
    # PRODUCT LINKS
    # ==================================================
    links = db.relationship(
        "ProductLink",
        backref="product",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ==================================================
    # TRACKED PRODUCTS
    # ==================================================
    tracked_items = db.relationship(
        "TrackedProduct",
        backref="tracked_product_ref",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Product {self.title}>"
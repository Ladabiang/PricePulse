from datetime import datetime, timezone
from app.extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)

    action = db.Column(
        db.String(255),
        nullable=False,
        index=True
    )

    username = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    ip_address = db.Column(
        db.String(50),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    def __repr__(self):
        return f"<ActivityLog {self.action}>"
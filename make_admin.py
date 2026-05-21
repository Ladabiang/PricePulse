import sys
from app import create_app
from app.extensions import db
from app.models.user import User


def promote_to_admin(email):

    app = create_app()

    with app.app_context():

        # ✅ FIXED: avoid User.query in scripts
        user = db.session.query(User).filter_by(
            email=email.strip().lower()
        ).first()

        if not user:
            print("❌ User not found.")
            return

        if user.role == "admin":
            print("⚠ Already admin")
            return

        user.role = "admin"
        db.session.commit()

        print("✅ Success: User promoted to admin")
        print(f"Email: {user.email}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python make_admin.py email@example.com")
        sys.exit(1)

    promote_to_admin(sys.argv[1])
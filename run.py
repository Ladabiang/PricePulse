# ==================================================
# run.py
# MAIN ENTRY POINT
# ==================================================

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app

# Create Flask app
app = create_app()

print("Starting Flask server...")


# ==================================================
# LOCAL DEVELOPMENT SERVER
# ==================================================
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
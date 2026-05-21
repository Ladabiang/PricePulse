from flask_mail import Message
from flask import current_app
from extensions import mail


def send_price_alert(user, product, price, target, url):

    msg = Message(
        subject="🚨 Price Drop Alert - PricePulse",
        recipients=[user.email]
    )

    msg.body = f"""
Hello {user.username},

Good news!

{product.title}

Current Price: ₹{price}
Your Target Price: ₹{target}

Buy Now:
{url}

Thanks,
PricePulse Team
"""

    mail.send(msg)
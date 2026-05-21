# ==================================================
# app/services/email_service.py
# PricePulse Email Alert Service
# ==================================================

from flask_mail import Message
from flask import current_app

from app.extensions import mail


def send_price_drop_email(
    user_email,
    product_name,
    old_price,
    new_price,
    product_url
):
    """
    Sends price drop / target price reached email to user.
    """

    try:
        if not user_email:
            print("EMAIL ERROR: No user email provided")
            return False

        subject = "Price Alert - PricePulse"

        msg = Message(
            subject=subject,
            recipients=[user_email],
            sender=current_app.config.get("MAIL_DEFAULT_SENDER")
        )

        msg.body = f"""
Hello,

Good news from PricePulse!

Your tracked product has reached your target price or changed in price.

Product:
{product_name}

Old Price: ₹{old_price}
New Price: ₹{new_price}

View Product:
{product_url}

Thanks,
PricePulse Smart Tracker
"""

        msg.html = f"""
        <div style="font-family:Arial,sans-serif;background:#f4f7fb;padding:25px;">
            <div style="max-width:650px;margin:auto;background:white;border-radius:14px;
                        padding:25px;border:1px solid #e5e7eb;">

                <h2 style="color:#0f172a;margin-bottom:10px;">
                    PricePulse Price Alert
                </h2>

                <p style="font-size:15px;color:#334155;">
                    Good news! Your tracked product has reached your target price
                    or changed in price.
                </p>

                <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">

                <h3 style="color:#111827;">
                    {product_name}
                </h3>

                <p style="font-size:16px;">
                    <b>Old Price:</b> ₹{old_price}
                </p>

                <p style="font-size:16px;">
                    <b>New Price:</b>
                    <span style="color:#16a34a;font-weight:bold;">
                        ₹{new_price}
                    </span>
                </p>

                <p style="margin-top:25px;">
                    <a href="{product_url}"
                       style="background:#38bdf8;color:white;padding:12px 20px;
                              border-radius:8px;text-decoration:none;font-weight:bold;">
                        View Product
                    </a>
                </p>

                <br>

                <p style="font-size:13px;color:#64748b;">
                    This email was sent because you are tracking this product on PricePulse.
                </p>

                <p style="font-size:13px;color:#64748b;">
                    — PricePulse Smart Tracker
                </p>
            </div>
        </div>
        """

        mail.send(msg)

        print(f"EMAIL SENT TO: {user_email}")

        return True

    except Exception as e:
        print("EMAIL ERROR:", e)
        return False
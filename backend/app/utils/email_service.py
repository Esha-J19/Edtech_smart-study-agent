import smtplib
from email.message import EmailMessage
import random
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_otp(email: str):
    otp = str(random.randint(100000, 999999))

    msg = EmailMessage()
    msg["Subject"] = "Your Verification Code"
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg.set_content(f"""
Your OTP for Smart Study Agent is:

{otp}

Do not share this code with anyone.
""")

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    return otp


import os
import smtplib
import keyring
from email.message import EmailMessage
from dotenv import load_dotenv
from config.secrets import get_secret
load_dotenv()

async def send_latest_bill_to_email(filePath):
  try:
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = get_secret("SENDER_EMAIL")
    password = get_secret("SENDER_EMAIL_PASS")
    to_email = get_secret("TO_EMAIL")

    if not sender_email or not password or not to_email:
        raise SystemExit("required information not specified.")
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        # Send email logic
        message = EmailMessage()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = "Latest Bill"
        message.set_content("Please find the latest bill attached. Send to Gideon.")
        
        with open(filePath, "rb") as f:
          message.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(filePath),
          )

        server.send_message(message)
        print(f"Email sent successfully from {sender_email}")

    return True
  except Exception as e:
    print(f"Failed to send email: {e}")
    return False


async def send_final_attempt_failure_email(year_month):
  try:
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = get_secret("SENDER_EMAIL")
    password = get_secret("SENDER_EMAIL_PASS")
    to_email = get_secret("TO_EMAIL")

    if not sender_email or not password or not to_email:
        raise SystemExit("required information not specified.")
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        message = EmailMessage()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = f"Municipal bill for {year_month} unavailable"
        message.set_content(
          f"The municipal bill for {year_month} had still not been published on the final "
          "attempt of the 25th. No statement was downloaded this month."
        )

        server.send_message(message)
        print(f"Final attempt failure email sent from {sender_email}")

    return True
  except Exception as e:
    print(f"Failed to send email: {e}")
    return False

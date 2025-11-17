import os
from twilio.rest import Client
from dotenv import load_dotenv
from apiGateway.ngrok import expose_file_via_ngrok, stop_ngrok_tunnel
# Load environment variables from a .env file
load_dotenv()

async def send_latest_bill_via_whatsapp(filePath):
  try:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        raise SystemExit("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in your environment variables.")

    client = Client(account_sid, auth_token)

    public_file_url = await create_public_url(filePath)

    message = client.messages.create(
            from_='whatsapp:+14155238886',
            media_url=[public_file_url],
            body="Here is your latest municipal bill.", # You can optionally include a body with the media
            to='whatsapp:+27XXXXXXXXX'
        )
    print(message.sid)
    print(f"Message sent successfully with SID: {message.sid}")

    # close the ngrok tunnel after sending the message
    await stop_ngrok_tunnel()
    return True

  except Exception as e:
    print(f"Failed to send message: {e}")
    return False

async def create_public_url(filePath):
    public_file_url = await expose_file_via_ngrok(filePath)
    return public_file_url
   
   
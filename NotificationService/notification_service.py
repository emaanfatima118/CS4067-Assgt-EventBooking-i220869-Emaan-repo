import pika
import json
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='notification_queue')

def callback(ch, method, properties, body):
    data = json.loads(body)
    user_email = data.get("user_email")
    
    if not user_email:
        print("Missing user email!")
        return

    message = f"Booking confirmed for Event {data['event_id']}!"
    send_email(user_email, message)


def send_email(user_email, message):
# Load environment variables from .env file

# Retrieve values from .env
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEText(message)
    msg["Subject"] = "Booking Confirmation"
    msg["From"] = sender_email
    msg["To"] = user_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        print(f"Email sent to {user_email}")
    except Exception as e:
        print(f"Email failed: {e}")

channel.basic_consume(queue='notification_queue', on_message_callback=callback, auto_ack=True)
print("Waiting for notifications...")
channel.start_consuming()

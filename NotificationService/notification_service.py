import pika
import json
import smtplib
from email.mime.text import MIMEText

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare Queue
channel.queue_declare(queue='notification_queue')

def callback(ch, method, properties, body):
    data = json.loads(body)
    user_email = data.get("user_email", "default@example.com")  # You should get actual user email
    message = f"Booking confirmed for Event {data['event_id']}!"
    send_email(user_email, message)

def send_email(user_email, message):
    sender_email = "your-email@example.com"
    password = "your-email-password"

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
        print(f"📧 Email sent to {user_email}")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")
# Consume Messages from RabbitMQ
channel.basic_consume(queue='notification_queue', on_message_callback=callback, auto_ack=True)

print(" Waiting for notifications...")
channel.start_consuming()

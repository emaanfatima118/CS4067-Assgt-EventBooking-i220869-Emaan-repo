from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import pika
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.String, nullable=False)
    tickets = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, default="PENDING")

#  Create Tables
with app.app_context():
    db.create_all()

#  Retrieve All Bookings
@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([{
        "booking_id": b.id,
        "user_id": b.user_id,
        "event_id": b.event_id,
        "tickets": b.tickets,
        "status": b.status
    } for b in bookings])

#  Booking Route
@app.route('/bookings', methods=['POST'])
def book_ticket():
    data = request.json
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    tickets = data.get("tickets")

    if not user_id or not event_id or not tickets:
        return jsonify({"error": "Missing required fields"}), 400

    # Check Event Availability (Call Event Service)
    try:
        event_response = requests.get(f"http://localhost:8000/events/{event_id}")
        event_response.raise_for_status()
        event = event_response.json()
    except requests.RequestException as e:
        print(f"Event Service Error: {e}")
        return jsonify({"error": "Event Service unavailable"}), 500

    if event["tickets_available"] < tickets:
        return jsonify({"error": "Not enough tickets available"}), 400

    # Process Payment (Mock Payment API)
    try:
        payment_response = requests.post("http://localhost:9000/payments", json={"user_id": user_id, "amount": tickets * 50})
        payment_response.raise_for_status()
        payment_data = payment_response.json()
    except requests.RequestException as e:
        print(f"Payment Service Error: {e}")
        return jsonify({"error": "Payment Service unavailable"}), 500

    if payment_data.get("status") != "PAID":
        return jsonify({"error": "Payment failed"}), 400

    # Update Event Tickets (Call Event Service)
    try:
        update_tickets_response = requests.put(
            f"http://localhost:8000/events/{event_id}/update_tickets",
            json={"tickets_sold": tickets},
            headers={"Content-Type": "application/json"}
        )
        update_tickets_response.raise_for_status()
    except requests.RequestException as e:
        print(f"Event Ticket Update Error: {e}")
        return jsonify({"error": "Failed to update event tickets"}), 500

    # Save Booking in Database
    try:
        new_booking = Booking(user_id=user_id, event_id=event_id, tickets=tickets, status="CONFIRMED")
        db.session.add(new_booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Database error"}), 500

    # Notify User (RabbitMQ)
    send_notification(user_id, event_id)

    return jsonify({"message": "Booking successful", "booking_id": new_booking.id})

# RabbitMQ Notification
def send_notification(user_id, event_id):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='notification_queue')

        notification_data = {
            "user_id": user_id,
            "event_id": event_id,
            "message": "Your booking is confirmed!"
        }

        channel.basic_publish(exchange='', routing_key='notification_queue', body=json.dumps(notification_data))
        print(f" Sent notification for User {user_id} - Event {event_id}")

        connection.close()
    except Exception as e:
        print(f" RabbitMQ Error: {e}")

# Home Route
@app.route('/')
def home():
    return {"message": "Welcome to the Booking Service!"}

# Run Flask App
if __name__ == '__main__':
    app.run(port=5000, debug=True)

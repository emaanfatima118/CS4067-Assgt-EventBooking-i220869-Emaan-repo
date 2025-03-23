from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Add this line
import requests
import pika
import os
import json
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
from functools import wraps
import secrets

# Generate a secret key (you can remove this after setting a proper .env value)
print(secrets.token_hex(32))

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)  # Ensure this is properly imported



SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
# Load Database Configurations from Environment Variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Booking Model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, nullable=False)
    tickets = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, default="PENDING")

# Create Tables
with app.app_context():
    db.create_all()

# Retrieve All Bookings
@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([{ "booking_id": b.id, "user_id": b.user_id, "event_id": b.event_id, "tickets": b.tickets, "status": b.status } for b in bookings])
def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing!"}), 403
        
        try:
            token = token.split(" ")[1]  
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 403

        return f(*args, **kwargs)
    return decorated

@app.route("/bookings", methods=["POST"])
@token_required  # Ensure authentication applies to the endpoint
def book_ticket():
    """Secure booking endpoint."""
    data = request.json
    user_id = request.user_id  # Extracted from JWT

    try:
        event_id = int(data.get("event_id"))
        tickets = int(data.get("tickets"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input data"}), 400

    if not event_id or tickets <= 0:
        return jsonify({"error": "Missing or invalid required fields"}), 400

    # Fetch User Email
    try:
        user_response = requests.get(f"http://localhost:8002/users/{user_id}")
        user_response.raise_for_status()
        user_email = user_response.json().get("email")
        if not user_email:
            return jsonify({"error": "User email not found!"}), 400
    except requests.RequestException:
        return jsonify({"error": "User Service unavailable"}), 500

    # Check Event Availability
    try:
        event_response = requests.get(f"http://localhost:8000/events/{event_id}")
        event_response.raise_for_status()
        event = event_response.json()
    except requests.RequestException:
        return jsonify({"error": "Event Service unavailable"}), 500

    if event["tickets_available"] < tickets:
        return jsonify({"error": "Not enough tickets available"}), 400

    # Process Payment
    try:
        payment_response = requests.post("http://localhost:9000/payments", json={"user_id": user_id, "amount": tickets * 50})
        payment_response.raise_for_status()
        if payment_response.json().get("status") != "PAID":
            return jsonify({"error": "Payment failed"}), 400
    except requests.RequestException:
        return jsonify({"error": "Payment Service unavailable"}), 500

    # Update Event Tickets
    try:
        update_tickets_response = requests.put(f"http://localhost:8000/events/{event_id}/update_tickets", json={"tickets_sold": tickets})
        update_tickets_response.raise_for_status()
    except requests.RequestException:
        return jsonify({"error": "Failed to update event tickets"}), 500

    # Save Booking in Database
    try:
        new_booking = Booking(user_id=user_id, event_id=event_id, tickets=tickets, status="CONFIRMED")
        db.session.add(new_booking)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500

    # Send Notification
    send_notification(user_id, user_email, event_id)

    return jsonify({"message": "Booking successful", "booking_id": new_booking.id})

def book_ticket():
    data = request.json
    try:
        user_id = int(data.get("user_id"))
        event_id = int(data.get("event_id"))
        tickets = int(data.get("tickets"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input data"}), 400

    if not user_id or not event_id or tickets <= 0:
        return jsonify({"error": "Missing or invalid required fields"}), 400

    # Fetch User Email
    try:
        user_response = requests.get(f"http://localhost:8002/users/{user_id}")
        user_response.raise_for_status()
        user_email = user_response.json().get("email")
        if not user_email:
            return jsonify({"error": "User email not found!"}), 400
    except requests.RequestException as e:
        return jsonify({"error": "User Service unavailable"}), 500

    # Check Event Availability
    try:
        event_response = requests.get(f"http://localhost:8000/events/{event_id}")
        event_response.raise_for_status()
        event = event_response.json()
    except requests.RequestException:
        return jsonify({"error": "Event Service unavailable"}), 500

    if event["tickets_available"] < tickets:
        return jsonify({"error": "Not enough tickets available"}), 400

    # Process Payment
    try:
        payment_response = requests.post("http://localhost:9000/payments", json={"user_id": user_id, "amount": tickets * 50})
        payment_response.raise_for_status()
        if payment_response.json().get("status") != "PAID":
            return jsonify({"error": "Payment failed"}), 400
    except requests.RequestException:
        return jsonify({"error": "Payment Service unavailable"}), 500

    # Update Event Tickets
    try:
        update_tickets_response = requests.put(f"http://localhost:8000/events/{event_id}/update_tickets", json={"tickets_sold": tickets})
        update_tickets_response.raise_for_status()
    except requests.RequestException:
        return jsonify({"error": "Failed to update event tickets"}), 500

  
    try:
        new_booking = Booking(user_id=user_id, event_id=event_id, tickets=tickets, status="CONFIRMED")
        db.session.add(new_booking)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500

  
    send_notification(user_id, user_email, event_id)
    return jsonify({"message": "Booking successful", "booking_id": new_booking.id})
@app.route('/bookings/user/<string:user_id>', methods=['GET'])
@token_required  # Ensure only authenticated users access their bookings
def get_user_bookings(user_id):
    """Retrieve all bookings for a specific user."""
    user_bookings = Booking.query.filter_by(user_id=user_id).all()
    
    if not user_bookings:
        return jsonify({"message": "No bookings found for this user"}), 404

    return jsonify([
        {
            "booking_id": booking.id,
            "event_id": booking.event_id,
            "tickets": booking.tickets,
            "status": booking.status
        }
        for booking in user_bookings
    ])

def send_notification(user_id, user_email, event_id):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='notification_queue')
        notification_data = { "user_id": user_id, "user_email": user_email, "event_id": event_id, "message": "Your booking is confirmed!" }
        channel.basic_publish(exchange='', routing_key='notification_queue', body=json.dumps(notification_data))
        connection.close()
    except Exception as e:
        print(f"RabbitMQ Error: {e}")

# Home Route
@app.route('/')
def home():
    return {"message": "Welcome to the Booking Service!"}

# Run Flask App
if __name__ == '__main__':
    app.run(port=5000, debug=True)

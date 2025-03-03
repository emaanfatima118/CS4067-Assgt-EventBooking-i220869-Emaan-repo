# CS4067-Assgt-EventBooking-22i-0869-Emaan-repo
Event Booking System

Team Members:

Emaan Fatima (22i-0869)

Aden Sial (22i-1313)

Overview

A web-based event booking system designed to let users seamlessly browse, book, and manage events. This system follows a microservices architecture, ensuring scalability and modularity by maintaining separate services for user management, event handling, and booking operations.

📌 Features

User Authentication: Registration and Login functionality.

Event Management: Users can create, update, and delete events.

Booking System: Secure event reservations and booking management.

Microservices Architecture: Independent services improve scalability and maintainability.

Message Queue: Utilizes RabbitMQ for efficient inter-service communication.

RESTful APIs: Standardized endpoints for smooth frontend-backend interaction.

🏗️ System Architecture

This system consists of three main microservices:

🟢 User Service

Responsibilities: Manages user authentication and profiles.

Technology Stack:

Backend: Python (Flask)

Database: MongoDB

Communication: RESTful APIs, RabbitMQ

🔵 Event Service

Responsibilities: Handles event creation, updates, and deletions.

Technology Stack:

Backend: Python (Flask)

Database: MongoDB

Communication: RESTful APIs, RabbitMQ

🔴 Booking Service

Responsibilities: Manages event reservations and booking history.

Technology Stack:

Backend: Node.js (Express)

Database: MongoDB

Communication: RESTful APIs, RabbitMQ

📡 API Endpoints

🟢 User Service

Register a New User

POST /api/users/register

Request Body:

{
  "username": "johndoe",
  "email": "johndoe@example.com",
  "password": "securepassword"
}

Response:

{
  "message": "User registered successfully!",
  "userId": "unique_user_id"
}

User Login

POST /api/users/login

Request Body:

{
  "email": "johndoe@example.com",
  "password": "securepassword"
}

Response:

{
  "token": "jwt_token_here",
  "user": {
    "id": "unique_user_id",
    "username": "johndoe",
    "email": "johndoe@example.com"
  }
}

🔵 Event Service

Create a New Event

POST /api/events

Request Body:

{
  "title": "Tech Conference 2025",
  "description": "Annual technology event.",
  "date": "2025-06-15",
  "location": "New York",
  "availableSeats": 100
}

Response:

{
  "message": "Event created successfully!",
  "eventId": "unique_event_id"
}

🔴 Booking Service

Book an Event

POST /api/bookings

Request Body:

{
  "userId": "unique_user_id",
  "eventId": "unique_event_id"
}

Response:

{
  "message": "Booking confirmed!",
  "bookingId": "unique_booking_id"
}

🚀 Setup Guide

Prerequisites

Ensure the following dependencies are installed:

Node.js (v14+)

Python (v3.8+)

MongoDB (v4+)

RabbitMQ (v3+)

npm (v6+)

pip (latest version)

2️⃣ Setting Up Services

Each service is inside its respective directory.

🟢 User Service Setup

cd User_Service
python -m venv env
source env/bin/activate  # (Windows: .\env\Scripts\activate)
pip install -r requirements.txt

Create a .env file:

FLASK_APP=app.py
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/user_service_db

Run the service:

flask run --port=5001

🔵 Event Service Setup

cd Event_Service
python -m venv env
source env/bin/activate
pip install -r requirements.txt

Create a .env file:

FLASK_APP=app.py
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/event_service_db

Run the service:

flask run --port=5002

🔴 Booking Service Setup

cd Booking_Service
npm install

Create a .env file:

PORT=5003
MONGO_URI=mongodb://localhost:27017/booking_service_db

Run the service:

node server.js

3️⃣ Start RabbitMQ

Ensure RabbitMQ is installed and running:

rabbitmq-server


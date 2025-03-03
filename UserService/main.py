from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson import ObjectId
import requests

app = FastAPI()

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
users_collection = db["users"]

# User Model
class User(BaseModel):
    username: str
    email: EmailStr
    password: str

# Login Model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/register")
async def register_user(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = {
        "username": user.username,
        "email": user.email,
        "password": user.password 
    }

    users_collection.insert_one(new_user)
    return {"message": "User registered successfully"}

@app.post("/login")
async def login_user(login_request: LoginRequest):
    """Logs in a user with a plain-text password check."""
    user = users_collection.find_one({"email": login_request.email})

    # Step 1: Check if user exists
    if not user:
        raise HTTPException(status_code=404, detail="User not registered")

    # Step 2: Compare passwords directly (plain-text)
    if login_request.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid password")

    # Step 3: Return success message if credentials match
    return {
        "message": "Login successful",
        "user": {
            "_id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }

@app.get("/users")
async def get_users():
    users = list(users_collection.find({}, {"password": 0}))  # Exclude passwords
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
    return users

@app.get("/events")
async def get_available_events():
    try:
        response = requests.get("http://localhost:8000/events")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Event Service Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events")

    return response.json()


@app.post("/book_event")
async def book_event(user_id: str, event_id: str, tickets: int):
    """Books an event for a user by calling the Booking Service."""
    if not users_collection.find_one({"_id": ObjectId(user_id)}):
        raise HTTPException(status_code=404, detail="User not found")

    try:
        response = requests.post(
            "http://localhost:5000/bookings",
            json={"user_id": user_id, "event_id": event_id, "tickets": tickets}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Booking Service Error: {e}")
        raise HTTPException(status_code=500, detail="Booking failed")

    return response.json()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson import ObjectId
import bcrypt

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

# Hash Password Function
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Register User
@app.post("/register")
async def register_user(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(user.password)

    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    }

    users_collection.insert_one(new_user)
    return {"message": "User registered successfully"}

# Get All Users (without passwords)
@app.get("/users")
async def get_users():
    users = list(users_collection.find({}, {"password": 0}))  # Exclude passwords
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
    return users
import requests
# Get events
@app.get("/events")
async def get_available_events():
    response = requests.get("http://localhost:8000/events")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch events")
    return response.json()
# book events
@app.post("/book_event")
async def book_event(user_id: str, event_id: str, tickets: int):
    response = requests.post(
        "http://localhost:5000/bookings",
        json={"user_id": user_id, "event_id": event_id, "tickets": tickets}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Booking failed")
    return response.json()

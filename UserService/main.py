from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from jose import JWTError, jwt
from datetime import datetime, timedelta,timezone
from fastapi import Security
from bson.objectid import ObjectId
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests
from fastapi import Path
from bson.objectid import ObjectId 
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

# Allow frontend origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
users_collection = db["users"]
counters_collection = db["counters"]

# JWT Secret Key and Algorithm
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Fallback to a hardcoded key for testing
    SECRET_KEY = "40aeebcf684c4cfb8c6e9f300e32866f9fad16d0cae975fb1b7074531445177a"

# Debug print to verify the key is loaded correctly
print(f"Secret key type: {type(SECRET_KEY)}, length: {len(SECRET_KEY) if SECRET_KEY else 'None'}")


ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
# Make sure the SECRET_KEY is properly loaded as a string


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/protected-route")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "You have access", "token": token}

# Ensure counter document exists
if counters_collection.find_one({"_id": "user_id"}) is None:
    counters_collection.insert_one({"_id": "user_id", "seq": 0})


class userid(BaseModel):
    user_id: int

def get_next_user_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "user_id"},  
        {"$inc": {"seq": 1}},  
        return_document=ReturnDocument.AFTER,
        upsert=True  
    )
    
    if counter is None:
        raise Exception("Counter document not found or not updating.")
    
    return counter["seq"]
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

    new_user_id = get_next_user_id()
    
    if users_collection.find_one({"_id": new_user_id}): 
        new_user_id = get_next_user_id() 

    new_user = {
        "_id": new_user_id,
        "username": user.username,
        "email": user.email,
        "password": user.password
    }

    users_collection.insert_one(new_user)
    return {"message": "User registered successfully", "user_id": new_user["_id"]}


@app.post("/login")
async def login_user(login_request: LoginRequest):
    user = users_collection.find_one({"email": login_request.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not registered")

    if login_request.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "message": "Login successful",
        "user": {
            "user_id": user["_id"],  # Integer ID
            "username": user["username"],
            "email": user["email"]
        }
    }



@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = users_collection.find_one({"_id": user_id}, {"password": 0})  # Ensure `_id` is int

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.get("/users")
async def get_users():
    users = list(users_collection.find({}, {"password": 0}))  # Exclude passwords
    for user in users:
        user["_id"] = int(user["_id"])  # Ensure integer format
    return users
def create_access_token(data: dict, expires_delta: timedelta):
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login_for_access_token(request: LoginRequest):  # Expect JSON input
    user = users_collection.find_one({"email": request.email})
    if not user or request.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["_id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/usersme")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    print("🔹 Received Token:", token)  # Debugging Step 1

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("🔹 Decoded Payload:", payload)  # Debugging Step 2

        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token (no user_id)")

        print("🔹 Extracted User ID:", user_id)  # Debugging Step 3

        user = users_collection.find_one({"_id": user_id}, {"password": 0})  
        print("🔹 User Fetched from DB:", user)  # Debugging Step 4

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError as e:
        print("🔴 JWT Error:", str(e))  # Debugging Step 5
        raise HTTPException(status_code=401, detail="Invalid token")



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
async def book_event(user_id: int, event_id: int, tickets: int):
    """Books an event for a user by calling the Booking Service."""
    if not users_collection.find_one({"_id": user_id}):  # Use integer `_id`
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

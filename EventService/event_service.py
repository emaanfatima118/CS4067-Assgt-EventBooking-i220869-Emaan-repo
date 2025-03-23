from fastapi import FastAPI, HTTPException, Body
from pymongo import MongoClient, ReturnDocument
from pydantic import BaseModel
from bson import ObjectId
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["event_db"]
events_collection = db["events"]
counters_collection = db["counters"] 

def get_next_event_id():
    # Find the highest existing event ID in the collection
    max_event = events_collection.find_one({}, sort=[("_id", -1)], projection={"_id": 1})

    counter = counters_collection.find_one_and_update(
        {"_id": "event_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        projection={"sequence_value": 1, "_id": 0}
    )

    # Ensure the counter starts from the next available number
    if not counter:  
        new_start = max_event["_id"] + 1 if max_event else 1
        counters_collection.insert_one({"_id": "event_id", "sequence_value": new_start})
        return new_start

    # If counter exists but is behind existing IDs, update it
    if max_event and counter["sequence_value"] <= max_event["_id"]:
        new_start = max_event["_id"] + 1
        counters_collection.update_one({"_id": "event_id"}, {"$set": {"sequence_value": new_start}})
        return new_start

    return counter["sequence_value"]


class Event(BaseModel):
    name: str
    description: str
    date: str
    location: str
    tickets_available: int

class TicketUpdate(BaseModel):
    tickets_sold: int

# Create Event (Auto-incrementing ID)
@app.post("/events")
def add_event(event: Event):
    existing_event = events_collection.find_one({"name": event.name})
    if existing_event:
        raise HTTPException(status_code=400, detail="An event with this name already exists")

    if event.tickets_available <= 0:
        raise HTTPException(status_code=400, detail="Tickets must be greater than zero")

    new_event = {
        "_id": get_next_event_id(),  # Assigning an integer ID
        "name": event.name,
        "description": event.description,
        "date": event.date,
        "location": event.location,
        "tickets_available": event.tickets_available,
    }

    events_collection.insert_one(new_event)
    return {"message": "Event added successfully", "event_id": new_event["_id"]}

@app.get("/events")
def list_events():
    try:
        events = list(events_collection.find({}, {"_id": 1, "name": 1, "date": 1, "tickets_available": 1}))

        # Convert ObjectId to string
        for event in events:
            event["_id"] = str(event["_id"])

        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

# Get Event by ID
@app.get("/events/{event_id}")
def get_event(event_id: int):
    event = events_collection.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Update Tickets After Booking
@app.put("/events/{event_id}/update_tickets")
def update_event_tickets(event_id: int, update_data: TicketUpdate = Body(...)):
    event = events_collection.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if "tickets_available" not in event:
        raise HTTPException(status_code=500, detail="Event does not have a 'tickets_available' field")

    new_tickets_available = event["tickets_available"] - update_data.tickets_sold
    if new_tickets_available < 0:
        raise HTTPException(status_code=400, detail="Not enough tickets available")

    events_collection.update_one({"_id": event_id}, {"$set": {"tickets_available": new_tickets_available}})
    return {"message": "Tickets updated", "remaining_tickets": new_tickets_available}

# Check Ticket Availability
@app.get("/events/{event_id}/availability")
def check_event_availability(event_id: int):
    event = events_collection.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"event_id": event["_id"], "tickets_available": event["tickets_available"]}

# Delete Event
@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    result = events_collection.delete_one({"_id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

# Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel

app = FastAPI()

#Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["event_db"]
events_collection = db["events"]  # Collection to store events

# Define a Pydantic Model for Ticket Updates
class TicketUpdate(BaseModel):
    tickets_sold: int

# Endpoint to Get All Events
@app.get("/events")
def list_events():
    events = list(events_collection.find({}, {"_id": 0}))  # Exclude MongoDB ID
    return {"events": events}

# Endpoint to Get a Single Event by ID
@app.get("/events/{event_id}")
def get_event(event_id: str):
    try:
        event = events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        event["_id"] = str(event["_id"])  # Convert ObjectId to string
        return event
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid event ID: {str(e)}")

# Endpoint to Update Tickets After Booking
@app.put("/events/{event_id}/update_tickets")
def update_event_tickets(event_id: str, update_data: TicketUpdate):
    try:
        event = events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        if "tickets_available" not in event:
            raise HTTPException(status_code=500, detail="Event does not have a 'tickets_available' field")

        new_tickets_available = event["tickets_available"] - update_data.tickets_sold
        if new_tickets_available < 0:
            raise HTTPException(status_code=400, detail="Not enough tickets available")

        events_collection.update_one({"_id": ObjectId(event_id)}, {"$set": {"tickets_available": new_tickets_available}})
        return {"message": "Tickets updated", "remaining_tickets": new_tickets_available}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating tickets: {str(e)}")
    
@app.get("/events/{event_id}/availability")
def check_event_availability(event_id: str):
    try:
        event = events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        if "tickets_available" not in event:
            raise HTTPException(status_code=500, detail="Event does not have a 'tickets_available' field")

        return {"event_id": str(event["_id"]), "tickets_available": event["tickets_available"]}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error checking availability: {str(e)}")


# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

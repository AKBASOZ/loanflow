from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="LoanFlow Notification Mock")

class NotificationRequest(BaseModel):
    application_id: str
    status: str

NOTIFICATION_STATE = {
    "notifications": [],
    "call_count": 0,
}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/notify")
def notify(payload: NotificationRequest):
    NOTIFICATION_STATE["call_count"] += 1
    NOTIFICATION_STATE["notifications"].append(payload.model_dump())
    return {"message": "Notification received"}

@app.get("/notifications")
def get_notifications():
    return {
        "call_count": NOTIFICATION_STATE["call_count"],
        "notifications": NOTIFICATION_STATE["notifications"],
    }

@app.post("/__admin/reset")
def reset_notifications():
    NOTIFICATION_STATE["notifications"] = []
    NOTIFICATION_STATE["call_count"] = 0
    return {"message": "Notification state reset"}
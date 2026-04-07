from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone
import httpx


app = FastAPI(title="LoanFlow Application API")


RISK_ENGINE_URL = "http://127.0.0.1:8001/score"
NOTIFICATION_URL = "http://127.0.0.1:8002/notify"
RISK_ENGINE_TIMEOUT_SECONDS = 5.0
IDEMPOTENCY_WINDOW_SECONDS = 60


APPLICATIONS = []


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


class ApplicationRequest(BaseModel):
    applicant_name: str = Field(min_length=1, max_length=100)
    annual_income: float = Field(ge=0)
    requested_amount: float = Field(ge=1000, le=500000)
    employment_status: str
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("employment_status")
    @classmethod
    def validate_employment_status(cls, value: str) -> str:
        allowed = {"employed", "self_employed", "unemployed", "retired"}
        if value not in allowed:
            raise ValueError(f"employment_status must be one of {sorted(allowed)}")
        return value


class ApplicationResponse(BaseModel):
    id: str
    applicant_name: str
    annual_income: float
    requested_amount: float
    employment_status: str
    status: str
    risk_score: Optional[int]
    decision_reason: str
    created_at: str
    updated_at: str
    notes: Optional[str] = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: List[str] = []


def normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def find_idempotent_match(applicant_name: str, requested_amount: float):
    now = utc_now()
    normalized_name = normalize_name(applicant_name)

    for app_record in reversed(APPLICATIONS):
        same_name = normalize_name(app_record["applicant_name"]) == normalized_name
        same_amount = app_record["requested_amount"] == requested_amount
        age_seconds = (now - datetime.fromisoformat(app_record["created_at"])).total_seconds()

        if same_name and same_amount and age_seconds <= IDEMPOTENCY_WINDOW_SECONDS:
            return app_record

    return None


def call_risk_engine(payload: dict) -> dict:
    with httpx.Client(timeout=RISK_ENGINE_TIMEOUT_SECONDS) as client:
        response = client.post(RISK_ENGINE_URL, json=payload)
        response.raise_for_status()
        return response.json()


def send_notification(application_id: str, status: str) -> None:
    try:
        with httpx.Client(timeout=3.0) as client:
            client.post(
                NOTIFICATION_URL,
                json={"application_id": application_id, "status": status},
            )
    except Exception:
        # For this challenge, notification delivery failure is not fatal to application creation.
        pass


def determine_decision(
    annual_income: float,
    requested_amount: float,
    employment_status: str,
    risk_score: Optional[int],
) -> tuple[str, str]:
    if risk_score is None:
        return "error", "Risk Engine timeout or unavailable"

    ratio = annual_income / requested_amount if requested_amount else 0

    if employment_status == "unemployed" and requested_amount > 10000:
        return "rejected", "Unemployed applicant requesting more than 10000"

    if risk_score < 30:
        return "rejected", "Risk score below rejection threshold"

    if risk_score >= 70 and ratio >= 2.0:
        return "approved", "Meets auto-approval threshold"

    return "pending", "Requires manual review"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/applications", response_model=ApplicationResponse, status_code=201)
def create_application(payload: ApplicationRequest):
    existing = find_idempotent_match(payload.applicant_name, payload.requested_amount)
    if existing:
        return existing

    risk_score = None

    try:
        risk_response = call_risk_engine(payload.model_dump(exclude_none=True))
        risk_score = risk_response.get("risk_score")
    except Exception:
        risk_score = None

    status, decision_reason = determine_decision(
        annual_income=payload.annual_income,
        requested_amount=payload.requested_amount,
        employment_status=payload.employment_status,
        risk_score=risk_score,
    )

    timestamp = iso_now()
    application = {
        "id": str(uuid4()),
        "applicant_name": payload.applicant_name,
        "annual_income": payload.annual_income,
        "requested_amount": payload.requested_amount,
        "employment_status": payload.employment_status,
        "status": status,
        "risk_score": risk_score,
        "decision_reason": decision_reason,
        "created_at": timestamp,
        "updated_at": timestamp,
        "notes": payload.notes,
    }

    APPLICATIONS.append(application)
    send_notification(application["id"], application["status"])
    return application


@app.get("/applications", response_model=List[ApplicationResponse])
def list_applications(status: Optional[str] = Query(default=None)):
    if status is None:
        return APPLICATIONS

    allowed = {"pending", "approved", "rejected", "error"}
    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid status filter",
                "details": [f"status must be one of {sorted(allowed)}"],
            },
        )

    return [app_record for app_record in APPLICATIONS if app_record["status"] == status]


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: str):
    for app_record in APPLICATIONS:
        if app_record["id"] == application_id:
            return app_record

    raise HTTPException(
        status_code=404,
        detail={
            "error_code": "NOT_FOUND",
            "message": f"Application {application_id} not found",
            "details": [],
        },
    )


@app.post("/__admin/reset")
def reset_applications():
    APPLICATIONS.clear()
    return {"message": "Application state reset"}
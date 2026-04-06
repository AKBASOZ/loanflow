from fastapi import FastAPI
from pydantic import BaseModel, Field
import time

app = FastAPI(title="LoanFlow Risk Engine Mock")

class RiskEngineRequest(BaseModel):
    applicant_name: str
    annual_income: float = Field(ge=0)
    requested_amount: float = Field(ge=1000, le=500000)
    employment_status: str

class RiskEngineResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    recommendation: str

class MockConfig(BaseModel):
    risk_score: int = Field(default=50, ge=0, le=100)
    recommendation: str = "manual_review"
    delay_seconds: float = Field(default=0, ge=0)

MOCK_STATE = {
    "risk_score": 50,
    "recommendation": "manual_review",
    "delay_seconds": 0,
    "call_count": 0,
    "last_request": None,
}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/__admin/config")
def set_mock_config(config: MockConfig):
    MOCK_STATE["risk_score"] = config.risk_score
    MOCK_STATE["recommendation"] = config.recommendation
    MOCK_STATE["delay_seconds"] = config.delay_seconds
    return {
        "message": "Mock configuration updated",
        "config": {
            "risk_score": MOCK_STATE["risk_score"],
            "recommendation": MOCK_STATE["recommendation"],
            "delay_seconds": MOCK_STATE["delay_seconds"],
        },
    }


@app.post("/__admin/reset")
def reset_mock():
    MOCK_STATE["risk_score"] = 50
    MOCK_STATE["recommendation"] = "manual_review"
    MOCK_STATE["delay_seconds"] = 0
    MOCK_STATE["call_count"] = 0
    MOCK_STATE["last_request"] = None
    return {"message": "Mock state reset"}


@app.get("/__admin/state")
def get_mock_state():
    return MOCK_STATE


@app.post("/score", response_model=RiskEngineResponse)
def score_application(payload: RiskEngineRequest):
    MOCK_STATE["call_count"] += 1
    MOCK_STATE["last_request"] = payload.model_dump()

    delay = MOCK_STATE["delay_seconds"]
    if delay > 0:
        time.sleep(delay)

    return RiskEngineResponse(
        risk_score=MOCK_STATE["risk_score"],
        recommendation=MOCK_STATE["recommendation"],
    )

import uuid
import httpx


APPLICATION_API_URL = "http://127.0.0.1:8000"
RISK_ENGINE_ADMIN_URL = "http://127.0.0.1:8001/__admin"
NOTIFICATION_ADMIN_URL = "http://127.0.0.1:8002"
TIMEOUT = 10.0


def generate_application_payload(
    applicant_name=None,
    annual_income=65000,
    requested_amount=25000,
    employment_status="employed",
    notes="Robot test payload",
):
    if applicant_name is None:
        applicant_name = f"Applicant-{uuid.uuid4().hex[:8]}"

    return {
        "applicant_name": applicant_name,
        "annual_income": annual_income,
        "requested_amount": requested_amount,
        "employment_status": employment_status,
        "notes": notes,
    }


def configure_risk_engine_mock(risk_score=50, recommendation="manual_review", delay_seconds=0):
    payload = {
        "risk_score": int(risk_score),
        "recommendation": recommendation,
        "delay_seconds": float(delay_seconds),
    }

    response = httpx.post(
        f"{RISK_ENGINE_ADMIN_URL}/config",
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def reset_risk_engine_mock():
    response = httpx.post(
        f"{RISK_ENGINE_ADMIN_URL}/reset",
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_risk_engine_mock_state():
    response = httpx.get(
        f"{RISK_ENGINE_ADMIN_URL}/state",
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def reset_notification_mock():
    response = httpx.post(
        f"{NOTIFICATION_ADMIN_URL}/__admin/reset",
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_notifications():
    response = httpx.get(
        f"{NOTIFICATION_ADMIN_URL}/notifications",
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def reset_application_api_state():
    response = httpx.post(
        f"{APPLICATION_API_URL}/__admin/reset",
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def should_be_same_application_id(first_id, second_id):
    if first_id != second_id:
        raise AssertionError(
            f"Expected same application id, but got '{first_id}' and '{second_id}'"
        )


def should_have_notification_for_status(notifications_response, expected_status):
    notifications = notifications_response.get("notifications", [])

    for item in notifications:
        if item.get("status") == expected_status:
            return

    raise AssertionError(
        f"No notification found with status '{expected_status}'. "
        f"Notifications: {notifications}"
    )
import uuid
import httpx


class LoanFlowKeywords:
    def __init__(self):
        self.application_api_url = "http://127.0.0.1:8000"
        self.risk_engine_admin_url = "http://127.0.0.1:8001/__admin"
        self.notification_admin_url = "http://127.0.0.1:8002"
        self.timeout = 10.0

    def generate_application_payload(
        self,
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

    def configure_risk_engine_mock(self, risk_score=50, recommendation="manual_review", delay_seconds=0):
        payload = {
            "risk_score": int(risk_score),
            "recommendation": recommendation,
            "delay_seconds": float(delay_seconds),
        }

        response = httpx.post(
            f"{self.risk_engine_admin_url}/config",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def reset_risk_engine_mock(self):
        response = httpx.post(
            f"{self.risk_engine_admin_url}/reset",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_risk_engine_mock_state(self):
        response = httpx.get(
            f"{self.risk_engine_admin_url}/state",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def reset_notification_mock(self):
        response = httpx.post(
            f"{self.notification_admin_url}/__admin/reset",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_notifications(self):
        response = httpx.get(
            f"{self.notification_admin_url}/notifications",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def reset_application_api_state(self):
        response = httpx.post(
            f"{self.application_api_url}/__admin/reset",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def should_be_same_application_id(self, first_id, second_id):
        if first_id != second_id:
            raise AssertionError(
                f"Expected same application id, but got '{first_id}' and '{second_id}'"
            )

    def should_have_notification_for_status(self, notifications_response, expected_status):
        notifications = notifications_response.get("notifications", [])

        for item in notifications:
            if item.get("status") == expected_status:
                return

        raise AssertionError(
            f"No notification found with status '{expected_status}'. "
            f"Notifications: {notifications}"
        )
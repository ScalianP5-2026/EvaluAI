from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard_summary_endpoint() -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "total_employees" in payload
    assert "usage_distribution" in payload


def test_chat_query_endpoint() -> None:
    response = client.post(
        "/api/v1/chat/query",
        json={
            "employee_role": "Technology",
            "learning_goal": "Python avanzado para ML",
            "ai_usage": "sometimes",
            "self_efficacy": 6.5,
            "motivation": 7.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "recommended_courses" in payload
    assert "thirty_day_plan" in payload


def test_nlp_endpoint() -> None:
    response = client.post(
        "/api/v1/nlp/analyze",
        json={
            "comments": [
                "Great support from mentor",
                "Training was difficult and confusing",
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "overall_sentiment" in payload
    assert "topics" in payload

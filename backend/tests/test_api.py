"""
API Integration Tests for EvaluAI Backend

Tests only the ACTIVE endpoints registered in main.py.
Endpoints are organized by router:

ACTIVE ROUTERS:
- chat_routes.py: POST /api/v1/chat/query, GET /api/v1/chat/history
- kpi_routes.py: GET /api/v1/kpi/summary
- main.py: GET /api/v1/health, GET /api/v1/config, GET /

DEPRECATED (not tested):
- routes.py endpoints (POST /api/v1/chat/query, GET /api/v1/dashboard/summary, 
  POST /api/v1/surveys/upload, POST /api/v1/nlp/analyze) are no longer registered.
  See app/api/routes.py for deprecation notice and migration path.
"""

import json
from unittest.mock import AsyncMock, MagicMock

from app.api import chat_routes
from app.chatbot.data_manager import DataManager
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test health check endpoint (registered in main.py)."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "service" in payload
    assert "version" in payload


def test_chat_query_endpoint() -> None:
    """Test chat query endpoint with mocked Supabase and Gemini dependencies.

    Supabase and Gemini are replaced via app.dependency_overrides so the test
    is isolated from external services and always returns a deterministic result.
    """
    # --- Mock DataManager (wraps Supabase queries) ---
    mock_dm = MagicMock(spec=DataManager)
    mock_dm.get_similar_profiles.return_value = {"count": 5}
    mock_dm.get_department_insights.return_value = {"count_employees": 10}
    mock_dm.get_top_courses.return_value = []

    # --- Mock Gemini client with a deterministic JSON response ---
    mock_gemini = MagicMock()
    mock_gemini.query = AsyncMock(
        return_value=json.dumps(
            {
                "message": "Here are your personalized recommendations.",
                "recommendations": {
                    "course": "Python for ML",
                    "rationale": "Ideal for your level",
                    "plan_30_days": ["Week 1: Basics", "Week 2: Advanced"],
                },
                "insights": {
                    "general": "72% of similar employees improved.",
                    "department": "Tech dept shows 25% improvement.",
                    "personal": "Based on your profile...",
                },
                "risk_alert": None,
            }
        )
    )

    # --- Mock Supabase client used for inserts inside the route handler ---
    mock_supabase = MagicMock()

    app.dependency_overrides[chat_routes.get_data_manager] = lambda: mock_dm
    app.dependency_overrides[chat_routes.get_gemini_client] = lambda: mock_gemini
    app.dependency_overrides[chat_routes.get_supabase_client] = lambda: mock_supabase

    try:
        response = client.post(
            "/api/v1/chat/query",
            json={
                "user_id": "test-employee-001",
                "message": "I want to learn Python for ML",
                "employee_context": {
                    "department": "Technology",
                    "education_level": "Bachelor",
                    "ai_usage_frequency": 3,
                    "motivation": 7.0,
                    "self_efficacy": 6.5,
                },
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert "message" in payload
        assert "session_id" in payload
        assert "insights" in payload
    finally:
        app.dependency_overrides.clear()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVED TESTS (Endpoints in deprecated routes.py, not registered)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# These endpoints were in app/api/routes.py but are NOT registered in main.py
# and NOT called by the frontend. They are kept below as reference.
# 
# If you need to restore these endpoints:
# 1. Review app/api/routes.py (at top: DEPRECATED notice with migration path)
# 2. Migrate logic to appropriate router
# 3. Uncomment import in app/api/__init__.py
# 4. Register in main.py
# 5. Uncomment tests below
# 6. Test thoroughly
#
# def test_dashboard_summary_endpoint() -> None:
#     """ARCHIVED: Endpoint in routes.py but not registered in main.py."""
#     response = client.get("/api/v1/dashboard/summary")
#     assert response.status_code == 200
#     payload = response.json()
#     assert "total_employees" in payload
#
#
# def test_nlp_endpoint() -> None:
#     """ARCHIVED: Endpoint in routes.py but not registered in main.py."""
#     response = client.post(
#         "/api/v1/nlp/analyze",
#         json={
#             "comments": [
#                 "Great support from mentor",
#                 "Training was difficult and confusing",
#             ]
#         },
#     )
#     assert response.status_code == 200
#     payload = response.json()
#     assert "overall_sentiment" in payload
#     assert "topics" in payload
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

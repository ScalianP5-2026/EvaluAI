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
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch

from app.api import chat_routes
from app.chatbot.data_manager import DataManager
from app.models.auth_schemas import EmployeeInfo
from app.main import app
from fastapi.testclient import TestClient

try:
    from backend.routes import nlp_routes as nlp_routes_module
except ImportError:
    from routes import nlp_routes as nlp_routes_module  # type: ignore

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
    mock_dm.get_employee_context.return_value = {
        "employee_id": "test-employee-001",
        "department": "Technology",
        "education_level": "Bachelor",
        "ai_usage_frequency": 3,
        "motivation": 7.0,
        "self_efficacy": 6.5,
        "age": 30,
        "years_in_company": 3,
    }
    mock_dm.get_retrieved_facts_for_query.return_value = {
        "source": "structured_db_retrieval",
        "scope": ["identity", "ai_usage"],
        "facts": {},
    }
    mock_dm.get_similar_profiles.return_value = {
        "summary": "5 similar employees",
        "avg_improvement": 24,
    }
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

    # Make history preload return empty deterministic data.
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])

    # --- Mock auxiliary services used inside the route ---
    mock_hybrid_instance = MagicMock()
    mock_hybrid_instance.run.return_value = {
        "ranked_courses": [],
        "ranked_mentors": [],
        "recommended_programs": [],
        "query_understanding": {},
        "tool_trace": [],
        "evaluation": {},
        "citations": [],
    }

    mock_ml_client = MagicMock()
    mock_ml_client.get_employee_scores.return_value = {
        "recommendation_score": 0.75,
        "risk_score": 0.2,
        "confidence": 0.9,
        "model_available": True,
    }

    app.dependency_overrides[chat_routes.get_data_manager] = lambda: mock_dm
    app.dependency_overrides[chat_routes.get_gemini_client] = lambda: mock_gemini
    app.dependency_overrides[chat_routes.get_supabase_client] = lambda: mock_supabase
    app.dependency_overrides[chat_routes.get_current_user] = lambda: EmployeeInfo(
        employee_id="test-employee-001",
        email="test@example.com",
        department="Technology",
        age=30,
        gender=None,
        education_level="Bachelor",
        years_in_company=3,
    )

    try:
        with patch.object(chat_routes, "HybridRAGOrchestrator", return_value=mock_hybrid_instance), patch.object(chat_routes, "get_ml_client", return_value=mock_ml_client), patch.object(chat_routes, "record_hybrid_rag_event", return_value=None):
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


def test_nlp_summary_endpoint() -> None:
    """Test NLP summary endpoint returns aggregated sentiment/topic/NPI payloads."""
    original_get_sentiment_summary = nlp_routes_module.get_sentiment_summary
    original_get_topic_summary = nlp_routes_module.get_topic_summary
    original_get_npi_distribution = nlp_routes_module.get_npi_distribution

    nlp_routes_module.get_sentiment_summary = lambda: {
        "status": "ok",
        "sentiment_counts": {"positive": 10, "neutral": 5},
    }
    nlp_routes_module.get_topic_summary = lambda: {
        "status": "ok",
        "topic_counts": {"0": 8, "1": 7},
    }
    nlp_routes_module.get_npi_distribution = lambda: {
        "status": "ok",
        "npi_category_counts": {"moderate_risk": 9, "high_risk": 6},
    }

    try:
        response = client.get("/api/nlp/summary")
        assert response.status_code == 200
        payload = response.json()
        assert "sentiment" in payload
        assert "topic" in payload
        assert "npi_distribution" in payload
        assert payload["sentiment"]["status"] == "ok"
    finally:
        nlp_routes_module.get_sentiment_summary = original_get_sentiment_summary
        nlp_routes_module.get_topic_summary = original_get_topic_summary
        nlp_routes_module.get_npi_distribution = original_get_npi_distribution


def test_nlp_strategic_summary_endpoint() -> None:
    """Test NLP strategic summary endpoint shape and successful status."""
    original_get_strategic_summary = nlp_routes_module.get_strategic_summary
    nlp_routes_module.get_strategic_summary = lambda: {
        "status": "ok",
        "kpis": {
            "high_ai_autonomy_dependency_risk_percent": 52.5,
            "neutral_sentiment_percent": 47.5,
            "avg_npi_score": 0.46,
            "top_risk_topic": "0",
        },
    }

    try:
        response = client.get("/api/nlp/strategic-summary")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert "kpis" in payload
    finally:
        nlp_routes_module.get_strategic_summary = original_get_strategic_summary


def test_nlp_employee_endpoint_found() -> None:
    """Test NLP employee endpoint returns profile payload for existing employee."""
    original_get_employee_nlp = nlp_routes_module.get_employee_nlp
    nlp_routes_module.get_employee_nlp = lambda employee_id: {
        "status": "ok",
        "employee_id": employee_id,
        "sentiment_label": "neutral",
    }

    try:
        response = client.get("/api/nlp/employee/emp-001")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["employee_id"] == "emp-001"
    finally:
        nlp_routes_module.get_employee_nlp = original_get_employee_nlp


def test_nlp_employee_endpoint_not_found() -> None:
    """Test NLP employee endpoint returns 404 when employee profile is missing."""
    original_get_employee_nlp = nlp_routes_module.get_employee_nlp
    nlp_routes_module.get_employee_nlp = lambda employee_id: {
        "status": "not_found",
        "employee_id": employee_id,
        "message": "Employee not found",
    }

    try:
        response = client.get("/api/nlp/employee/missing-employee")
        assert response.status_code == 404
        payload = response.json()
        assert "detail" in payload
        assert payload["detail"]["status"] == "not_found"
    finally:
        nlp_routes_module.get_employee_nlp = original_get_employee_nlp


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

"""
Pytest configuration and fixtures for chatbot tests.

Provides mocks and fixtures for testing chatbot core components.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_gemini_response():
    """Mock successful Gemini API response."""
    return """{
    "message": "Great! Machine Learning is an excellent choice.",
    "recommendations": {
        "course": "ML Masterclass",
        "mentor": "Data Science Lead",
        "plan_30_days": [
            "Week 1: Review Python fundamentals",
            "Week 2: Study ML algorithms and theory",
            "Week 3: Build first ML project",
            "Week 4: Deploy and optimize model"
        ]
    },
    "insights": {
        "general": "81% of professionals who studied ML improved their career prospects",
        "department": "Tech department shows 28% average improvement in AI skills",
        "personal": "Your self-efficacy suggests you can successfully master advanced ML concepts"
    },
    "metadata": {
        "goal_detected": true,
        "goal_clarity": "high",
        "recommended_skill": "Machine Learning"
    },
    "risk_alert": null
}"""


@pytest.fixture
def mock_malformed_response():
    """Mock malformed response that's not valid JSON."""
    return """Let me help you with that! 
    {
    "message": "Here's what I recommend...",
    This is not valid JSON"""


@pytest.fixture
def mock_empty_response():
    """Mock empty response."""
    return ""


@pytest.fixture
def mock_user_context() -> Dict[str, Any]:
    """Fixture for employee user context."""
    return {
        "employee_id": "1XVWCBPH",
        "department": "Technology",
        "education_level": "Master",
        "ai_usage_frequency": 4,
        "motivation": 7.5,
        "self_efficacy": 8.0,
        "seniority": "Senior",
    }


@pytest.fixture
def mock_rag_context() -> Dict[str, Any]:
    """Fixture for RAG SQL enriched context."""
    return {
        "similar_profiles_summary": "12 employees in similar role improved 25% on average",
        "department_insights": "Tech dept shows high variability in AI adoption (25%-85%)",
        "top_courses": [
            {"title": "ML Masterclass", "completion_rate": 0.85},
            {"title": "Python Advanced", "completion_rate": 0.78},
        ],
        "avg_improvement": 25,
        "risk_flags": [],
    }


@pytest.fixture
def mock_conversation_history():
    """Fixture for conversation history."""
    return [
        {"role": "user", "content": "I want to learn Machine Learning"},
        {
            "role": "assistant",
            "content": "ML is great. Here are some recommendations...",
        },
    ]


@pytest.fixture
def mock_api_key():
    """Fixture for mock API key."""
    return "test-api-key-12345"


@pytest.mark.asyncio
async def mock_async_gemini_call():
    """Mock async Gemini API call."""
    return """{"message": "test response", "recommendations": {}}"""


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )

"""
Unit tests for response_parser.

Tests JSON parsing, fallback handling, and validation.
"""

import pytest
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.chatbot.response_parser import (
    parse_response,
    validate_response_structure,
)


@pytest.mark.unit
class TestResponseParser:
    """Test suite for response parsing."""

    def test_parse_valid_json_response(self, mock_gemini_response):
        """Test parsing valid JSON response from Gemini."""
        result = parse_response(mock_gemini_response)

        assert result is not None
        assert result["success"] is True
        assert "message" in result
        assert "recommendations" in result
        assert "insights" in result
        assert result["raw"] == mock_gemini_response

    def test_parse_response_contains_message(self, mock_gemini_response):
        """Test that parsed response contains message field."""
        result = parse_response(mock_gemini_response)

        assert result["message"] is not None
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_parse_response_contains_recommendations(self, mock_gemini_response):
        """Test that parsed response contains recommendations."""
        result = parse_response(mock_gemini_response)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], dict)
        assert "course" in result["recommendations"]
        assert "mentor" in result["recommendations"]
        assert "plan_30_days" in result["recommendations"]

    def test_parse_response_contains_insights(self, mock_gemini_response):
        """Test that parsed response contains insights."""
        result = parse_response(mock_gemini_response)

        assert "insights" in result
        assert isinstance(result["insights"], dict)
        assert "general" in result["insights"]
        assert "department" in result["insights"]
        assert "personal" in result["insights"]

    def test_parse_response_contains_metadata(self, mock_gemini_response):
        """Test that parsed response contains metadata."""
        result = parse_response(mock_gemini_response)

        assert "metadata" in result
        assert isinstance(result["metadata"], dict)
        assert "goal_detected" in result["metadata"]
        assert "goal_clarity" in result["metadata"]

    def test_parse_malformed_json_falls_back(self, mock_malformed_response):
        """Test that malformed JSON triggers fallback."""
        result = parse_response(mock_malformed_response)

        assert result is not None
        assert "message" in result
        assert result["success"] is False
        assert "Fall back" in result["message"]

    def test_parse_empty_response_falls_back(self, mock_empty_response):
        """Test that empty response triggers fallback."""
        result = parse_response(mock_empty_response)

        assert result is not None
        assert result["success"] is False
        assert "metadata" in result
        assert "recommendations" in result

    def test_parse_response_preserves_raw(self, mock_gemini_response):
        """Test that raw response is preserved in result."""
        result = parse_response(mock_gemini_response)

        assert result["raw"] == mock_gemini_response

    def test_parse_response_structure_validation(self, mock_gemini_response):
        """Test that parsed response passes validation."""
        result = parse_response(mock_gemini_response)

        is_valid = validate_response_structure(result)
        assert is_valid is True

    def test_validate_response_structure_positive(self):
        """Test validation with valid response structure."""
        valid_response = {
            "success": True,
            "message": "test",
            "recommendations": {},
            "insights": {},
            "raw": "test",
        }

        assert validate_response_structure(valid_response) is True

    def test_validate_response_structure_negative(self):
        """Test validation with missing required fields."""
        invalid_response = {
            "success": True,
            "message": "test",
            # Missing 'recommendations', 'insights', 'raw'
        }

        assert validate_response_structure(invalid_response) is False

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON nested in extra text."""
        response_with_extras = """
        Here's my response:
        {
            "message": "Hello",
            "recommendations": {
                "course": "ML101",
                "mentor": "Expert",
                "plan_30_days": []
            },
            "insights": {
                "general": "Test",
                "department": "Tech",
                "personal": "Good"
            },
            "metadata": {},
            "risk_alert": null
        }
        Additional explanation here.
        """

        result = parse_response(response_with_extras)

        assert result["success"] is True
        assert result["message"] == "Hello"
        assert result["recommendations"]["course"] == "ML101"

    def test_parse_response_with_null_values(self):
        """Test parsing response with null values."""
        response = json.dumps({
            "message": "Test",
            "recommendations": {
                "course": None,
                "mentor": None,
                "plan_30_days": [],
            },
            "insights": {
                "general": "Test",
                "department": None,
                "personal": "Test",
            },
            "metadata": {"goal_detected": False, "goal_clarity": "low"},
            "risk_alert": None,
        })

        result = parse_response(response)

        assert result["success"] is True
        assert result["recommendations"]["course"] is None
        assert result["insights"]["department"] is None

    def test_parse_response_missing_optional_fields(self):
        """Test that missing optional fields get defaults."""
        minimal_response = json.dumps({
            "message": "Test message",
            "recommendations": {"course": "ML101"},
            "insights": {"general": "Test"},
        })

        result = parse_response(minimal_response)

        assert result["success"] is True
        assert "metadata" in result
        assert "risk_alert" in result
        assert result["risk_alert"] is None

    def test_fallback_response_has_all_fields(self, mock_empty_response):
        """Test that fallback response includes all required fields."""
        result = parse_response(mock_empty_response)

        required_fields = [
            "success",
            "message",
            "recommendations",
            "insights",
            "raw",
            "metadata",
            "risk_alert",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_parse_response_with_nested_json(self):
        """Test parsing response with complex nested structure."""
        complex_response = json.dumps({
            "message": "Complex response",
            "recommendations": {
                "course": "Advanced ML",
                "mentor": "Expert",
                "plan_30_days": [
                    "Week 1: Learn basics",
                    "Week 2: Practice",
                    "Week 3: Project",
                    "Week 4: Review",
                ],
            },
            "insights": {
                "general": "Detailed insight 1",
                "department": "Detailed insight 2",
                "personal": "Detailed insight 3",
            },
            "metadata": {
                "goal_detected": True,
                "goal_clarity": "high",
                "recommended_skill": "ML",
            },
            "risk_alert": "high_concentration",
        })

        result = parse_response(complex_response)

        assert result["success"] is True
        assert len(result["recommendations"]["plan_30_days"]) == 4
        assert result["metadata"]["goal_detected"] is True
        assert result["risk_alert"] == "high_concentration"

    def test_parse_response_large_text(self):
        """Test parsing response with large message text."""
        large_message = "A" * 5000  # 5000 character message
        response = json.dumps({
            "message": large_message,
            "recommendations": {"course": "Test"},
            "insights": {"general": "Test"},
        })

        result = parse_response(response)

        assert result["success"] is True
        assert len(result["message"]) == 5000

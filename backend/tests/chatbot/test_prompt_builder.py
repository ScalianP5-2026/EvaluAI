"""
Unit tests for PromptBuilder.

Tests that prompts are correctly structured and include JSON format instructions.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.chatbot.prompt_builder import PromptBuilder


@pytest.mark.unit
class TestPromptBuilder:
    """Test suite for PromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Initialize PromptBuilder for tests."""
        return PromptBuilder()

    def test_initialization(self, builder):
        """Test PromptBuilder initializes correctly."""
        assert builder is not None
        assert builder.system_role is not None
        assert "JSON" in builder.system_role

    def test_goal_detection_keywords_present(self, builder):
        """Test that goal detection keywords are defined in settings."""
        from app.chatbot import settings
        assert len(settings.GOAL_DETECTION_KEYWORDS) > 0
        assert "learn" in settings.GOAL_DETECTION_KEYWORDS
        assert "improve" in settings.GOAL_DETECTION_KEYWORDS
        assert "master" in settings.GOAL_DETECTION_KEYWORDS

    def test_build_initial_prompt_basic(self, builder, mock_user_context):
        """Test building initial prompt with user context."""
        prompt = builder.build_initial_prompt(mock_user_context)

        assert prompt is not None
        assert len(prompt) > 0
        assert mock_user_context["department"] in prompt
        assert str(mock_user_context["motivation"]) in prompt

    def test_build_initial_prompt_includes_json_instruction(self, builder, mock_user_context):
        """Test that initial prompt includes mandatory JSON format section."""
        prompt = builder.build_initial_prompt(mock_user_context)

        assert "MANDATORY JSON RESPONSE FORMAT" in prompt
        assert "{" in prompt and "}" in prompt
        assert "Respond ONLY with JSON" in prompt
        assert '"message"' in prompt
        assert '"recommendations"' in prompt

    def test_build_initial_prompt_validates(self, builder, mock_user_context):
        """Test validation of initial prompt."""
        prompt = builder.build_initial_prompt(mock_user_context)
        is_valid = builder.validate_prompt_includes_json_instruction(prompt)

        assert is_valid is True

    def test_build_contextual_prompt_basic(
        self,
        builder,
        mock_user_context,
        mock_rag_context,
        mock_conversation_history,
    ):
        """Test building contextual prompt with all parameters."""
        user_message = "I want to become a data scientist"
        prompt = builder.build_contextual_prompt(
            user_message=user_message,
            user_context=mock_user_context,
            rag_context=mock_rag_context,
            history=mock_conversation_history,
        )

        assert prompt is not None
        assert len(prompt) > 0
        assert user_message in prompt
        assert mock_user_context["department"] in prompt

    def test_build_contextual_prompt_with_rag_context(
        self,
        builder,
        mock_user_context,
        mock_rag_context,
    ):
        """Test that RAG context is properly injected."""
        prompt = builder.build_contextual_prompt(
            user_message="What course should I take?",
            user_context=mock_user_context,
            rag_context=mock_rag_context,
            history=[],
        )

        assert mock_rag_context["similar_profiles_summary"] in prompt
        assert mock_rag_context["department_insights"] in prompt
        assert str(mock_rag_context["avg_improvement"]) in prompt

    def test_build_contextual_prompt_without_rag_context(
        self,
        builder,
        mock_user_context,
    ):
        """Test contextual prompt with None RAG context (fallback)."""
        prompt = builder.build_contextual_prompt(
            user_message="Help me learn",
            user_context=mock_user_context,
            rag_context=None,
            history=[],
        )

        assert prompt is not None
        assert "No similar profiles analyzed yet" in prompt
        assert "Department data being loaded" in prompt

    def test_build_contextual_prompt_includes_json_instruction(
        self,
        builder,
        mock_user_context,
        mock_rag_context,
    ):
        """Test that contextual prompt includes JSON format instruction."""
        prompt = builder.build_contextual_prompt(
            user_message="Test",
            user_context=mock_user_context,
            rag_context=mock_rag_context,
            history=[],
        )

        assert "MANDATORY JSON RESPONSE FORMAT" in prompt
        assert "Respond ONLY with JSON" in prompt
        assert '"message"' in prompt
        assert '"recommendations"' in prompt
        assert '"metadata"' in prompt

    def test_build_contextual_prompt_validates(
        self,
        builder,
        mock_user_context,
        mock_rag_context,
    ):
        """Test validation of contextual prompt."""
        prompt = builder.build_contextual_prompt(
            user_message="Test",
            user_context=mock_user_context,
            rag_context=mock_rag_context,
            history=[],
        )

        is_valid = builder.validate_prompt_includes_json_instruction(prompt)
        assert is_valid is True

    def test_build_contextual_prompt_with_history(
        self,
        builder,
        mock_user_context,
        mock_rag_context,
        mock_conversation_history,
    ):
        """Test that conversation history is included in prompt."""
        prompt = builder.build_contextual_prompt(
            user_message="Next question",
            user_context=mock_user_context,
            rag_context=mock_rag_context,
            history=mock_conversation_history,
        )

        # Check that history section is present
        assert "CONVERSATION HISTORY" in prompt
        for turn in mock_conversation_history:
            assert turn["content"] in prompt

    def test_build_initial_prompt_with_missing_fields(self, builder):
        """Test that initial prompt handles missing context fields gracefully."""
        minimal_context = {"department": "Tech"}

        prompt = builder.build_initial_prompt(minimal_context)

        assert prompt is not None
        assert "Tech" in prompt
        assert "Unknown" in prompt or "Mid-level" in prompt

    def test_prompt_builder_system_role_consistency(self, builder):
        """Test that system role is consistent across prompts."""
        prompt1 = builder.build_initial_prompt({"department": "A"})
        prompt2 = builder.build_initial_prompt({"department": "B"})

        # Both should start with system role
        assert prompt1.startswith(builder.system_role)
        assert prompt2.startswith(builder.system_role)

    def test_validate_prompt_positive(self, builder):
        """Test validation function returns True for valid prompt."""
        valid_prompt = """Some text
        MANDATORY JSON RESPONSE FORMAT
        {{ "test": "value" }}"""

        assert builder.validate_prompt_includes_json_instruction(valid_prompt) is True

    def test_validate_prompt_negative(self, builder):
        """Test validation function returns False for invalid prompt."""
        invalid_prompt = "Just a regular prompt without JSON instruction"

        assert builder.validate_prompt_includes_json_instruction(invalid_prompt) is False

    def test_build_contextual_prompt_top_courses_formatting(
        self,
        builder,
        mock_user_context,
    ):
        """Test that top courses are properly formatted in prompt."""
        rag_context = {
            "similar_profiles_summary": "...",
            "department_insights": "...",
            "top_courses": [
                {"title": "Course A", "completion_rate": 0.9},
                {"title": "Course B", "completion_rate": 0.8},
            ],
            "avg_improvement": 20,
            "risk_flags": [],
        }

        prompt = builder.build_contextual_prompt(
            user_message="Test",
            user_context=mock_user_context,
            rag_context=rag_context,
            history=[],
        )

        assert "Course A" in prompt
        assert "Course B" in prompt

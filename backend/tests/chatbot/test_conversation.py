"""
Unit tests for ConversationMemory.

Tests conversation tracking, metadata extraction, and goal detection.
"""

import pytest
from backend.app.chatbot.conversation import ConversationMemory


@pytest.mark.unit
class TestConversationMemory:
    """Test suite for ConversationMemory class."""

    @pytest.fixture
    def memory(self):
        """Initialize ConversationMemory for tests."""
        return ConversationMemory(employee_id="EMP_001")

    def test_initialization(self, memory):
        """Test ConversationMemory initializes correctly."""
        assert memory.employee_id == "EMP_001"
        assert len(memory.turns) == 0
        assert memory.max_turns == 10

    def test_add_single_turn(self, memory):
        """Test adding a single turn to memory."""
        memory.add_turn("user", "Hello, I want to learn Python")

        assert len(memory.turns) == 1
        assert memory.turns[0]["role"] == "user"
        assert "Python" in memory.turns[0]["content"]

    def test_add_multiple_turns(self, memory):
        """Test adding multiple turns."""
        memory.add_turn("user", "First message")
        memory.add_turn("assistant", "First response")
        memory.add_turn("user", "Second message")

        assert len(memory.turns) == 3
        assert memory.turns[0]["role"] == "user"
        assert memory.turns[1]["role"] == "assistant"

    def test_add_turn_invalid_role(self, memory):
        """Test that invalid role raises error."""
        with pytest.raises(ValueError):
            memory.add_turn("invalid", "message")

    def test_add_turn_empty_content(self, memory):
        """Test that empty content raises error."""
        with pytest.raises(ValueError):
            memory.add_turn("user", "")

    def test_add_turn_with_metadata(self, memory):
        """Test adding turn with additional metadata."""
        metadata = {"sentiment": 0.8, "intent": "learning"}
        memory.add_turn("user", "Test message", metadata=metadata)

        assert "metadata" in memory.turns[0]
        assert memory.turns[0]["metadata"]["sentiment"] == 0.8

    def test_get_history_format(self, memory):
        """Test that get_history returns correct format."""
        memory.add_turn("user", "Question")
        memory.add_turn("assistant", "Answer")

        history = memory.get_history()

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Question"
        assert history[1]["role"] == "assistant"

    def test_get_last_n_turns(self, memory):
        """Test getting last N turns."""
        for i in range(5):
            memory.add_turn("user", f"Message {i}")

        last_3 = memory.get_last_n_turns(n=3)

        assert len(last_3) == 3
        assert "Message 2" in last_3[0]["content"]
        assert "Message 4" in last_3[2]["content"]

    def test_get_last_n_turns_exceeds_history(self, memory):
        """Test getting more turns than exist."""
        memory.add_turn("user", "Only message")

        last_5 = memory.get_last_n_turns(n=5)

        assert len(last_5) == 1

    def test_clear_memory(self, memory):
        """Test clearing conversation memory."""
        memory.add_turn("user", "Message 1")
        memory.add_turn("assistant", "Response 1")

        assert len(memory.turns) == 2

        memory.clear()

        assert len(memory.turns) == 0

    def test_max_turns_enforcement(self, memory):
        """Test that memory respects max_turns limit."""
        # Add more than max_turns
        for i in range(15):
            memory.add_turn("user", f"Message {i}")

        assert len(memory.turns) == memory.max_turns
        assert "Message 14" in memory.turns[-1]["content"]
        assert "Message 0" not in [t["content"] for t in memory.turns]

    def test_extract_metadata_goal_detected(self, memory):
        """Test goal detection in metadata extraction."""
        memory.add_turn("user", "I want to learn Python and Machine Learning")
        memory.add_turn("assistant", "Great choice!")

        metadata = memory.extract_metadata()

        assert metadata["goal_detected"] is True
        assert metadata["primary_goal"] is not None
        assert "learn" in metadata["primary_goal"].lower()

    def test_extract_metadata_no_goal(self, memory):
        """Test metadata extraction without goal."""
        memory.add_turn("user", "What's the weather today?")

        metadata = memory.extract_metadata()

        assert metadata["goal_detected"] is False
        assert metadata["goal_clarity"] == "low"

    def test_extract_metadata_goal_clarity_high(self, memory):
        """Test high goal clarity detection."""
        memory.add_turn(
            "user",
            "I need to master Python programming within 3 months"
        )

        metadata = memory.extract_metadata()

        assert metadata["goal_detected"] is True
        assert metadata["goal_clarity"] == "high"

    def test_extract_metadata_skill_detection(self, memory):
        """Test skill detection in conversation."""
        memory.add_turn("user", "I want to learn Python and machine learning")

        metadata = memory.extract_metadata()

        detected_skills = metadata["detected_skills"]
        assert len(detected_skills) > 0
        # Check for Python or ML keywords
        assert any(
            keyword in " ".join(detected_skills).lower()
            for keyword in ["python", "machine learning", "ml"]
        )

    def test_extract_metadata_depth(self, memory):
        """Test conversation depth calculation."""
        memory.add_turn("user", "Q1")
        memory.add_turn("assistant", "A1")
        memory.add_turn("user", "Q2")

        metadata = memory.extract_metadata()

        assert metadata["conversation_depth"] == 3

    def test_extract_metadata_recommendation_detected(self, memory):
        """Test recommendation detection in metadata."""
        memory.add_turn("assistant", "I recommend the Python course")

        metadata = memory.extract_metadata()

        assert metadata["has_recommendation"] is True

    def test_extract_metadata_structure(self, memory):
        """Test that extracted metadata has required fields."""
        memory.add_turn("user", "Teach me AI")

        metadata = memory.extract_metadata()

        required_fields = [
            "conversation_depth",
            "goal_detected",
            "primary_goal",
            "goal_clarity",
            "detected_skills",
            "has_recommendation",
        ]

        for field in required_fields:
            assert field in metadata

    def test_to_dict_serialization(self, memory):
        """Test serializing conversation to dict."""
        memory.add_turn("user", "Learn ML")
        memory.add_turn("assistant", "Here's help")

        serialized = memory.to_dict()

        assert "employee_id" in serialized
        assert "turns" in serialized
        assert "metadata" in serialized
        assert len(serialized["turns"]) == 2

    def test_from_dict_deserialization(self, memory):
        """Test deserializing conversation from dict."""
        # Serialize first memory
        memory.add_turn("user", "Question")
        memory.add_turn("assistant", "Answer")
        serialized = memory.to_dict()

        # Deserialize to new memory
        new_memory = ConversationMemory.from_dict(serialized)

        assert new_memory.employee_id == memory.employee_id
        assert len(new_memory.turns) == len(memory.turns)
        assert new_memory.turns[0]["content"] == "Question"

    def test_multiple_goal_keywords(self, memory):
        """Test conversation with multiple goal keywords."""
        memory.add_turn(
            "user",
            "I want to improve my skills and master new technologies to advance my career"
        )

        metadata = memory.extract_metadata()

        assert metadata["goal_detected"] is True
        # Primary goal should be the first keyword found
        assert metadata["primary_goal"] is not None

    def test_skill_detection_multiple_skills(self, memory):
        """Test detection of multiple skills in one message."""
        memory.add_turn(
            "user",
            "I need to learn Python, machine learning, and cloud computing with AWS"
        )

        metadata = memory.extract_metadata()

        assert len(metadata["detected_skills"]) >= 2

    def test_timestamp_in_turns(self, memory):
        """Test that turns include timestamps."""
        memory.add_turn("user", "Message")

        assert "timestamp" in memory.turns[0]
        assert memory.turns[0]["timestamp"] is not None

    def test_goal_clarity_calculation_edge_cases(self, memory):
        """Test goal clarity with ambiguous messages."""
        # Low clarity: just mentions skill, no clear intent
        memory.clear()
        memory.add_turn("user", "Python is interesting")

        metadata = memory.extract_metadata()

        assert metadata["goal_clarity"] in ["low", "medium", "high"]

    def test_empty_conversation_metadata(self, memory):
        """Test metadata extraction from empty conversation."""
        metadata = memory.extract_metadata()

        assert metadata["conversation_depth"] == 0
        assert metadata["goal_detected"] is False
        assert metadata["goal_clarity"] == "low"
        assert len(metadata["detected_skills"]) == 0

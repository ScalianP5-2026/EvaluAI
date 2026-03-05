"""
Conversation Memory for EvaluAI Chatbot Core.

Tracks conversation history and extracts metadata without using AI.
Uses simple heuristics for goal detection.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history and metadata extraction.

    Features:
    - Stores up to 10 turns
    - Extracts goals using keyword detection
    - Calculates goal clarity levels
    - Serializable to/from dict
    """

    # Keywords for goal detection
    GOAL_KEYWORDS = [
        "learn",
        "improve",
        "develop",
        "advance",
        "study",
        "train",
        "certification",
        "master",
        "become",
    ]

    # Skills that can be detected
    SKILL_PATTERNS = [
        r"\b(python|java|javascript|ml|machine learning|ai|artificial intelligence)\b",
        r"\b(data science|data analysis|analytics)\b",
        r"\b(cloud|aws|azure|gcp)\b",
        r"\b(leadership|management|communication)\b",
        r"\b(agile|scrum|devops)\b",
        r"\b(sql|database|backend|frontend)\b",
    ]

    def __init__(self, employee_id: str):
        """
        Initialize conversation memory.

        Args:
            employee_id: Unique employee identifier
        """
        self.employee_id = employee_id
        self.turns: List[Dict[str, str]] = []
        self.max_turns = 10
        self.created_at = datetime.utcnow()

        logger.debug(f"ConversationMemory initialized for employee={employee_id}")

    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add a turn to conversation history.

        Args:
            role: "user" or "assistant"
            content: Message text
            metadata: Optional metadata dict

        Raises:
            ValueError: If role is invalid
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        turn = {
            "role": role,
            "content": content.strip(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            turn["metadata"] = metadata

        self.turns.append(turn)

        # Enforce max turns (keep oldest, remove newest if overflow)
        if len(self.turns) > self.max_turns:
            removed = self.turns.pop(0)
            logger.debug(f"Removed oldest turn due to max_turns limit (employee={self.employee_id})")

        logger.debug(f"Turn added: role={role}, content_len={len(content)}")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get full conversation history.

        Returns:
            List of turn dicts: [{"role": "user", "content": "..."}, ...]
        """
        return [{"role": t["role"], "content": t["content"]} for t in self.turns]

    def get_last_n_turns(self, n: int = 8) -> List[Dict[str, str]]:
        """
        Get last N turns for API calls (to stay within token limits).

        Args:
            n: Number of turns (default: 8)

        Returns:
            Last N turns in Gemini format
        """
        if n < 1:
            raise ValueError("n must be at least 1")

        history = self.get_history()
        return history[-n:] if history else []

    def clear(self) -> None:
        """Clear all turns from memory."""
        self.turns = []
        logger.info(f"Conversation cleared (employee={self.employee_id})")

    def extract_metadata(self) -> Dict:
        """
        Extract metadata from conversation using heuristics.

        Uses keyword matching to detect:
        - Goal presence and clarity
        - Detected skills
        - Conversation depth

        Returns:
            Dict with extracted metadata:
            {
                "conversation_depth": int,
                "goal_detected": bool,
                "primary_goal": str or None,
                "goal_clarity": "high" | "medium" | "low",
                "detected_skills": List[str],
                "has_recommendation": bool
            }
        """
        all_text = " ".join([t["content"].lower() for t in self.turns])

        # Goal detection
        goal_detected = any(
            keyword in all_text.lower() for keyword in self.GOAL_KEYWORDS
        )

        # Primary goal extraction (simplified)
        primary_goal = self._extract_goal(all_text)

        # Goal clarity calculation
        goal_clarity = self._calculate_goal_clarity(all_text, goal_detected)

        # Skill detection
        detected_skills = self._extract_skills(all_text)

        # Recommendation presence (check if 'recommendation' or 'course' mentioned)
        has_recommendation = any(
            word in all_text for word in ["recommendation", "course", "mentor", "plan"]
        )

        metadata = {
            "conversation_depth": len(self.turns),
            "goal_detected": goal_detected,
            "primary_goal": primary_goal,
            "goal_clarity": goal_clarity,
            "detected_skills": detected_skills,
            "has_recommendation": has_recommendation,
        }

        logger.debug(f"Metadata extracted: {metadata}")
        return metadata

    def _extract_goal(self, text: str) -> Optional[str]:
        """
        Extract primary learning goal from text.

        Args:
            text: Lowercased conversation text

        Returns:
            Goal description or None
        """
        # Simple pattern: find first occurrence of goal keyword + next words
        for keyword in self.GOAL_KEYWORDS:
            pattern = rf"{keyword}\s+([a-z\s]+?)(?:\.|,|$)"
            match = re.search(pattern, text)
            if match:
                goal_text = match.group(1).strip()
                # Clean up and limit length
                goal_text = " ".join(goal_text.split()[:5])
                return f"{keyword.capitalize()} {goal_text}" if goal_text else keyword.capitalize()

        return None

    def _calculate_goal_clarity(self, text: str, goal_detected: bool) -> str:
        """
        Calculate goal clarity level.

        Rules:
        - high: Contains verb + skill
        - medium: Contains skill only
        - low: No goal or skill detected

        Args:
            text: Lowercased text
            goal_detected: Whether goal keyword was found

        Returns:
            "high" | "medium" | "low"
        """
        if not goal_detected:
            return "low"

        has_skill = len(self._extract_skills(text)) > 0
        has_clear_verb = any(
            verb in text for verb in ["want to", "need to", "must", "should"]
        )

        if has_clear_verb and has_skill:
            return "high"
        elif has_skill:
            return "medium"
        else:
            return "low"

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills mentioned in text using regex patterns.

        Args:
            text: Lowercased conversation text

        Returns:
            List of detected skills
        """
        detected_skills = []

        for pattern in self.SKILL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Flatten if matches are tuples
                skills = [
                    m[0] if isinstance(m, tuple) else m
                    for m in matches
                ]
                detected_skills.extend(skills)

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in detected_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)

        return unique_skills

    def to_dict(self) -> Dict:
        """
        Serialize conversation to dict for persistence.

        Returns:
            Dict representation of conversation
        """
        return {
            "employee_id": self.employee_id,
            "created_at": self.created_at.isoformat(),
            "turns": self.turns,
            "metadata": self.extract_metadata(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationMemory":
        """
        Deserialize conversation from dict.

        Args:
            data: Dict with keys: employee_id, turns

        Returns:
            ConversationMemory instance
        """
        memory = cls(data["employee_id"])
        for turn in data.get("turns", []):
            memory.turns.append(turn)
        return memory

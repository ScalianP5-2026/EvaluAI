"""
Domain Tracking: Track conversational domains and training session insights.
Part of the chatbot context management system.
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class TrainingSessionTracker:
    """
    Tracks training-related domains and insights during a conversation session.
    
    Monitors:
    - Learning goals (identified from user messages)
    - Training modules mentioned
    - Skill gaps detected
    - AI usage patterns in training context
    - Session metadata (duration, turns, etc.)
    """
    
    def __init__(self, session_id: str, user_id: str):
        """
        Initialize session tracker.
        
        Args:
            session_id: Unique conversation session identifier
            user_id: Employee ID
        """
        self.session_id = session_id
        self.user_id = user_id
        self.start_time = datetime.utcnow()
        self.turn_count = 0
        self.identified_goals: List[str] = []
        self.mentioned_modules: List[str] = []
        self.skill_gaps: List[Dict] = []
        self.metadata: Dict = {}
        
        logger.info(f"TrainingSessionTracker initialized for session {session_id}")
    
    def track_goal(self, goal: str) -> None:
        """Record an identified learning goal."""
        if goal and goal not in self.identified_goals:
            self.identified_goals.append(goal)
            logger.debug(f"Goal tracked: {goal}")
    
    def track_module(self, module: str) -> None:
        """Record a mentioned training module."""
        if module and module not in self.mentioned_modules:
            self.mentioned_modules.append(module)
            logger.debug(f"Module tracked: {module}")
    
    def track_skill_gap(self, skill: str, confidence: float = 0.5) -> None:
        """Record a detected skill gap."""
        gap = {"skill": skill, "confidence": confidence, "timestamp": datetime.utcnow()}
        self.skill_gaps.append(gap)
        logger.debug(f"Skill gap tracked: {skill}")
    
    def increment_turn(self) -> None:
        """Increment conversation turn counter."""
        self.turn_count += 1
    
    def get_session_summary(self) -> Dict:
        """
        Get summary of tracked session data.
        
        Returns:
            Dictionary with session summary
        """
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "duration_seconds": duration,
            "turns": self.turn_count,
            "goals_identified": len(self.identified_goals),
            "modules_mentioned": len(self.mentioned_modules),
            "skill_gaps_detected": len(self.skill_gaps),
            "goals": self.identified_goals,
            "modules": self.mentioned_modules,
            "metadata": self.metadata
        }

"""
EvaluAI Chatbot Core Module

Pure chatbot logic without database or API dependencies.
Designed to integrate with RAG system (Comp2) and frontend (Comp3).
"""

from .conversation import ConversationMemory
from .gemini_client import GeminiChatClient
from .prompt_builder import PromptBuilder
from .response_parser import parse_llm_response, validate_response_structure

__all__ = [
    "GeminiChatClient",
    "PromptBuilder",
    "ConversationMemory",
    "parse_llm_response",
    "validate_response_structure",
]

"""
EvaluAI Chatbot Core Module

Pure chatbot logic without database or API dependencies.
Designed to integrate with RAG system (Comp2) and frontend (Comp3).
"""

from .conversation import ConversationMemory
from .foundry_client import FoundryChatClient
from .gemini_client import GeminiChatClient
from .prompt_builder import PromptBuilder
from .response_parser import parse_response, validate_response_structure

__all__ = [
    "FoundryChatClient",
    "GeminiChatClient",
    "PromptBuilder",
    "ConversationMemory",
    "parse_response",
    "validate_response_structure",
]

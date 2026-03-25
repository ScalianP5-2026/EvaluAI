"""
EvaluAI Chatbot Core Module.

Uses lazy imports for optional provider clients so lightweight modules can be
imported without requiring all third-party AI SDK dependencies.
"""

from .conversation import ConversationMemory
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


def __getattr__(name: str):
    if name == "FoundryChatClient":
        from .foundry_client import FoundryChatClient

        return FoundryChatClient
    if name == "GeminiChatClient":
        from .gemini_client import GeminiChatClient

        return GeminiChatClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

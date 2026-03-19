"""
Gemini Chat Client for EvaluAI Chatbot Core.

Handles async communication with Google Gemini 2.5 Flash API.
Implements retry logic, timeout handling, and structured logging.
"""

import asyncio
import logging
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package not found. "
        "Install with: pip install google-generativeai"
    )

from . import settings

logger = logging.getLogger(__name__)


class GeminiChatClient:
    """
    Async client for Google Gemini 2.5 Flash.

    Configuration loaded from environment variables (.env):
    - CHATBOT_GEMINI_MODEL: gemini-2.5-flash
    - CHATBOT_GEMINI_TEMPERATURE: 0.4 (for consistency)
    - CHATBOT_GEMINI_MAX_TOKENS: 800 (ensures concise responses)
    - CHATBOT_GEMINI_TIMEOUT_SECONDS: 30
    - CHATBOT_GEMINI_MAX_RETRIES: 3 attempts
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key for Gemini (overrides env variable)
            model: Model name (overrides env variable)

        Raises:
            ValueError: If api_key is empty
        """
        # Use provided values or fall back to settings
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        self.timeout_seconds = settings.GEMINI_TIMEOUT_SECONDS
        self.max_retries = settings.GEMINI_MAX_RETRIES

        if not self.api_key:
            raise ValueError("API key cannot be empty (set CHATBOT_GEMINI_API_KEY)")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )

        logger.info(f"GeminiChatClient initialized with model={self.model}")

    async def query(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Send prompt to Gemini and get response.

        Args:
            prompt: The system/user prompt to send
            history: Optional conversation history format:
                [{"role": "user", "content": "..."}, ...]

        Returns:
            Raw response text from Gemini

        Raises:
            RuntimeError: If all retry attempts fail
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Prepare conversation (convert history to Gemini format if needed)
        if history is None:
            history = []

        last_attempt_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Query attempt {attempt + 1}/{self.max_retries}")

                # Run async call with timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._send_request_to_gemini,
                        prompt,
                        history,
                    ),
                    timeout=self.timeout_seconds,
                )

                logger.info(
                    f"Query successful on attempt {attempt + 1}. "
                    f"Response length: {len(response)} chars"
                )
                return response

            except asyncio.TimeoutError:
                last_attempt_error = "Request timeout (30s exceeded)"
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.max_retries}: "
                    f"{last_attempt_error}"
                )

            except Exception as e:
                last_attempt_error = str(e)
                logger.warning(
                    f"Error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )

        # All retries failed
        error_msg = (
            f"Failed to get response from Gemini after {self.max_retries} attempts. "
            f"Last error: {last_attempt_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _send_request_to_gemini(
        self,
        prompt: str,
        history: List[Dict[str, str]],
    ) -> str:
        """
        Synchronous wrapper to send request to Gemini API.

        Args:
            prompt: The prompt to send
            history: Conversation history

        Returns:
            Response text from Gemini
        """
        # Build message content
        contents = []

        # Add history
        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            # Map to Gemini roles
            gemini_role = "user" if role == "user" else "model"
            contents.append({"role": gemini_role, "parts": [content]})

        # Add current prompt
        contents.append({"role": "user", "parts": [prompt]})

        # Send actual request to API
        response = self.client.generate_content(contents)

        return response.text

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text (future use for RAG v2).

        Args:
            text: Text to embed

        Returns:
            Vector embedding

        Note:
            Not implemented yet. Placeholder for RAG vectorial v2.
        """
        raise NotImplementedError(
            "Embedding generation will be implemented in RAG v2"
        )

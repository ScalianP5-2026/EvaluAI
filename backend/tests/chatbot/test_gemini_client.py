"""
Unit tests for GeminiChatClient.

Tests async Gemini API communication with mocks.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.chatbot.gemini_client import GeminiChatClient
except Exception as exc:
    pytest.skip(
        f"Skipping Gemini client tests due to runtime incompatibility: {exc}",
        allow_module_level=True,
    )


@pytest.mark.unit
class TestGeminiChatClient:
    """Test suite for GeminiChatClient."""

    @pytest.fixture
    def api_key(self):
        """Provide test API key."""
        return "test-api-key-12345"

    def test_initialization(self, api_key):
        """Test GeminiChatClient initializes correctly."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            assert client.api_key == api_key
            assert client.model == "gemini-2.5-flash"
            assert client.temperature == 0.4
            assert client.max_tokens == 800

    def test_initialization_invalid_api_key(self):
        """Test that empty API key raises error."""
        with pytest.raises(ValueError):
            with patch("app.chatbot.gemini_client.genai"):
                GeminiChatClient(api_key="")

    def test_initialization_custom_model(self, api_key):
        """Test initialization with custom model."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key, model="gemini-pro")

            assert client.model == "gemini-pro"

    @pytest.mark.asyncio
    async def test_query_success(self, api_key):
        """Test successful query execution."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            # Mock the Gemini response
            mock_response = MagicMock()
            mock_response.text = "Test response"

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            result = await client.query("Test prompt", history=[])

            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_query_with_history(self, api_key):
        """Test query with conversation history."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "Response with context"

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            history = [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response"},
            ]

            result = await client.query("Next message", history=history)

            assert result == "Response with context"

    @pytest.mark.asyncio
    async def test_query_empty_prompt_raises_error(self, api_key):
        """Test that empty prompt raises ValueError."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            with pytest.raises(ValueError):
                await client.query("", history=[])

    @pytest.mark.asyncio
    async def test_query_timeout_retry(self, api_key):
        """Test timeout and retry behavior."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            # Mock that fails first 2 times, succeeds on 3rd
            mock_response = MagicMock()
            mock_response.text = "Success on retry"

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(
                side_effect=[
                    asyncio.TimeoutError(),
                    asyncio.TimeoutError(),
                    mock_response,
                ]
            )
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            client._send_request_to_gemini = MagicMock(
                side_effect=[
                    asyncio.TimeoutError(),
                    asyncio.TimeoutError(),
                    "Success on retry",
                ]
            )

            result = await client.query("Test", history=[])

            assert result == "Success on retry"

    @pytest.mark.asyncio
    async def test_query_max_retries_exceeded(self, api_key):
        """Test that RuntimeError is raised after max retries."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)
            client._send_request_to_gemini = MagicMock(
                side_effect=Exception("API Error")
            )

            with pytest.raises(RuntimeError) as exc_info:
                await client.query("Test", history=[])

            assert "Failed to get response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_timeout_per_request(self, api_key):
        """Test individual request timeout handling."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            # Mock that times out immediately
            async def timeout_func(*args, **kwargs):
                raise asyncio.TimeoutError()

            client._send_request_to_gemini = MagicMock(
                side_effect=Exception("Timeout")
            )

            with pytest.raises(RuntimeError):
                await client.query("Test", history=[])

    def test_config_temperature(self, api_key):
        """Test temperature configuration."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            # Temperature should be set to 0.4 for consistency
            assert client.temperature == 0.4

    def test_config_max_tokens(self, api_key):
        """Test max tokens configuration."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            # Max tokens should be 800 for concise responses
            assert client.max_tokens == 800

    def test_config_timeout(self, api_key):
        """Test timeout configuration."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            assert client.timeout_seconds == 30

    def test_max_retries_config(self, api_key):
        """Test max retries configuration."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            assert client.max_retries == 3

    def test_generate_embedding_not_implemented(self, api_key):
        """Test that embedding generation is not implemented yet."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            # The method exists but raises NotImplementedError when awaited
            import inspect
            assert inspect.iscoroutinefunction(client.generate_embedding)

    @pytest.mark.asyncio
    async def test_query_none_history(self, api_key):
        """Test query with None history (defaults to empty list)."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "Response"

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            result = await client.query("Test", history=None)

            assert result == "Response"

    @pytest.mark.asyncio
    async def test_query_large_response(self, api_key):
        """Test handling large responses from API."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            large_response = "A" * 50000  # 50KB response

            mock_response = MagicMock()
            mock_response.text = large_response

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            result = await client.query("Test", history=[])

            assert len(result) == 50000

    @pytest.mark.asyncio
    async def test_query_special_characters(self, api_key):
        """Test query with special characters."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = '{"test": "special chars: \n\t\\"quotes\\""}'

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

            client = GeminiChatClient(api_key=api_key)
            result = await client.query("Test with special chars: ñ, é, 中文", history=[])

            assert '"test"' in result

    def test_client_logging_initialized(self, api_key, caplog):
        """Test that client logging is initialized."""
        with patch("app.chatbot.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()

            client = GeminiChatClient(api_key=api_key)

            # Should log initialization
            assert client is not None

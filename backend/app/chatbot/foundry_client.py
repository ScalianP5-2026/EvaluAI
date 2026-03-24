"""
Azure Foundry (Azure OpenAI endpoint) client for EvaluAI Chatbot Core.

Provides the same async query interface as GeminiChatClient so the API route
can switch providers without changing chatbot business logic.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from . import settings

logger = logging.getLogger(__name__)


def _build_chat_completions_url(
    endpoint: str,
    deployment: str,
    api_version: str,
) -> str:
    """
    Build a valid Azure OpenAI chat completions URL.

    Supported endpoint inputs:
    - Full chat completions URL:
      https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/chat/completions?api-version=...
    - Deployment root URL:
      https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>
    - Resource base URL:
      https://<resource>.cognitiveservices.azure.com
    """
    raw = endpoint.strip()
    if not raw:
        raise ValueError("Foundry endpoint cannot be empty")

    parsed = urlparse(raw)
    path = parsed.path or ""
    query = parse_qs(parsed.query)

    if path.endswith("/chat/completions"):
        query.setdefault("api-version", [api_version])
        rebuilt_query = urlencode(query, doseq=True)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                rebuilt_query,
                parsed.fragment,
            )
        )

    if "/openai/deployments/" in path:
        normalized_path = path.rstrip("/")
        if not normalized_path.endswith("/chat/completions"):
            normalized_path = f"{normalized_path}/chat/completions"
        query.setdefault("api-version", [api_version])
        rebuilt_query = urlencode(query, doseq=True)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                normalized_path,
                parsed.params,
                rebuilt_query,
                parsed.fragment,
            )
        )

    if not deployment:
        raise ValueError(
            "CHATBOT_FOUNDRY_DEPLOYMENT is required when endpoint is a resource URL"
        )

    base = raw.rstrip("/")
    return (
        f"{base}/openai/deployments/{deployment}/chat/completions"
        f"?api-version={api_version}"
    )


class FoundryChatClient:
    """
    Async client for Azure Foundry/Azure OpenAI chat completions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.FOUNDRY_API_KEY
        self.endpoint = endpoint or settings.FOUNDRY_ENDPOINT
        self.deployment = deployment or settings.FOUNDRY_DEPLOYMENT
        self.api_version = settings.FOUNDRY_API_VERSION
        self.temperature = settings.FOUNDRY_TEMPERATURE
        self.max_tokens = settings.FOUNDRY_MAX_TOKENS
        self.timeout_seconds = settings.FOUNDRY_TIMEOUT_SECONDS
        self.max_retries = settings.FOUNDRY_MAX_RETRIES
        self.system_prompt = settings.FOUNDRY_SYSTEM_PROMPT
        self.use_structured_outputs = settings.FOUNDRY_USE_STRUCTURED_OUTPUTS
        self.structured_schema_name = settings.FOUNDRY_STRUCTURED_SCHEMA_NAME
        self.structured_schema_strict = settings.FOUNDRY_STRUCTURED_SCHEMA_STRICT
        self._runtime_structured_outputs_enabled = self.use_structured_outputs

        if not self.api_key:
            raise ValueError("API key cannot be empty (set CHATBOT_FOUNDRY_API_KEY)")
        if not self.endpoint:
            raise ValueError(
                "Foundry endpoint cannot be empty (set CHATBOT_FOUNDRY_ENDPOINT)"
            )

        self.chat_completions_url = _build_chat_completions_url(
            endpoint=self.endpoint,
            deployment=self.deployment,
            api_version=self.api_version,
        )

        logger.info(
            "FoundryChatClient initialized with deployment=%s",
            self.deployment or "<from-endpoint>",
        )

    async def query(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Send prompt to Azure OpenAI chat completions and return assistant text.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        history = history or []
        messages: List[Dict[str, str]] = []

        if self.system_prompt and self.system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": self.system_prompt.strip(),
                }
            )

        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if not content:
                continue
            normalized_role = "assistant" if role == "assistant" else "user"
            messages.append({"role": normalized_role, "content": content})

        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self._runtime_structured_outputs_enabled:
            payload["response_format"] = self._build_structured_response_format()

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        last_error: Optional[str] = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.chat_completions_url,
                        headers=headers,
                        json=payload,
                    )
                response.raise_for_status()
                data = response.json()
                content = self._extract_assistant_content(data)
                if not content:
                    raise RuntimeError("Empty content in Foundry response")
                return content
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response else None
                if (
                    status_code in (400, 404, 422)
                    and self._runtime_structured_outputs_enabled
                ):
                    logger.warning(
                        "Foundry endpoint rejected structured outputs. "
                        "Retrying without response_format. status=%s",
                        status_code,
                    )
                    self._runtime_structured_outputs_enabled = False
                    payload.pop("response_format", None)
                    continue
                last_error = str(exc)
                logger.warning(
                    "Foundry query attempt %s/%s failed: %s",
                    attempt + 1,
                    self.max_retries,
                    last_error,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.6)
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Foundry query attempt %s/%s failed: %s",
                    attempt + 1,
                    self.max_retries,
                    last_error,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.6)

        raise RuntimeError(
            f"Failed to get response from Foundry after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def _build_structured_response_format(self) -> Dict[str, Any]:
        """Build JSON schema response format for strict parseable outputs."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": self.structured_schema_name,
                "strict": self.structured_schema_strict,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "message",
                        "recommendations",
                        "insights",
                        "metadata",
                        "risk_alert",
                    ],
                    "properties": {
                        "message": {"type": "string"},
                        "recommendations": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["course", "mentor", "plan_30_days"],
                            "properties": {
                                "course": {"type": ["string", "null"]},
                                "mentor": {"type": ["string", "null"]},
                                "rationale": {"type": ["string", "null"]},
                                "plan_30_days": {
                                    "type": ["array", "null"],
                                    "items": {"type": "string"},
                                },
                            },
                        },
                        "insights": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["general", "department", "personal"],
                            "properties": {
                                "general": {"type": "string"},
                                "department": {"type": "string"},
                                "personal": {"type": "string"},
                            },
                        },
                        "metadata": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "goal_detected",
                                "goal_clarity",
                                "recommended_skill",
                            ],
                            "properties": {
                                "goal_detected": {"type": "boolean"},
                                "goal_clarity": {"type": "string"},
                                "recommended_skill": {"type": ["string", "null"]},
                            },
                        },
                        "risk_alert": {"type": ["string", "null"]},
                    },
                },
            },
        }

    @staticmethod
    def _extract_assistant_content(data: Dict[str, Any]) -> str:
        """
        Extract assistant content from Azure OpenAI response payload.

        Handles both plain-string and list-based content shapes.
        """
        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: List[str] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
            return "\n".join(text_parts).strip()
        return str(content or "")

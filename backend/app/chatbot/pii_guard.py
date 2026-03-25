"""
PII guard utilities for anonymizing data before LLM calls.

This module provides deterministic placeholder-based anonymization and
server-side rehydration for chatbot payloads.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


class PIIGuard:
    """Anonymize/de-anonymize personal data with deterministic placeholders."""

    _EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    _PHONE_REGEX = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
    _EMPLOYEE_ID_REGEX = re.compile(r"\b(?:EMP[-_ ]?\d{2,}|[A-Z]{2,6}\d{3,})\b")
    _PLACEHOLDER_REGEX = re.compile(r"\[(?:EMAIL|PHONE|PERSON|ID|CONTACT|VALUE)_\d+\]")

    _SENSITIVE_KEYWORDS = (
        "name",
        "nombre",
        "email",
        "mail",
        "phone",
        "telefono",
        "tel",
        "mobile",
        "teams",
        "contact",
    )

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._value_to_token: dict[str, str] = {}
        self._token_to_value: dict[str, str] = {}
        self._category_counts: defaultdict[str, int] = defaultdict(int)

    def anonymize_text(self, text: str) -> str:
        """Replace common PII patterns and registered values in text."""
        if not self.enabled or not isinstance(text, str) or not text:
            return text

        anonymized = text

        anonymized = self._EMAIL_REGEX.sub(
            lambda match: self._token_for("EMAIL", match.group(0)),
            anonymized,
        )
        anonymized = self._PHONE_REGEX.sub(
            lambda match: self._replace_phone_match(match.group(0)),
            anonymized,
        )
        anonymized = self._EMPLOYEE_ID_REGEX.sub(
            lambda match: self._token_for("ID", match.group(0)),
            anonymized,
        )

        # Replace any previously registered sensitive literals.
        for value, token in sorted(
            self._value_to_token.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if value and value in anonymized:
                anonymized = anonymized.replace(value, token)

        return anonymized

    def has_unmasked_pii_text(self, text: str) -> bool:
        """Detect whether unmasked direct-identifier patterns are present."""
        if not self.enabled or not isinstance(text, str) or not text:
            return False

        if self._EMAIL_REGEX.search(text):
            return True
        if self._EMPLOYEE_ID_REGEX.search(text):
            return True
        for match in self._PHONE_REGEX.finditer(text):
            if self._is_valid_phone_candidate(match.group(0)):
                return True
        return False

    def has_unmasked_pii_structure(self, payload: Any) -> bool:
        """Recursively detect whether a structure still includes direct identifiers."""
        if not self.enabled:
            return False
        if isinstance(payload, dict):
            return any(self.has_unmasked_pii_structure(value) for value in payload.values())
        if isinstance(payload, list):
            return any(self.has_unmasked_pii_structure(item) for item in payload)
        if isinstance(payload, str):
            return self.has_unmasked_pii_text(payload)
        return False

    def anonymize_structure(self, payload: Any) -> Any:
        """Recursively anonymize strings and sensitive-key scalar values."""
        if not self.enabled:
            return payload

        if isinstance(payload, dict):
            anonymized: dict[str, Any] = {}
            for key, value in payload.items():
                if self._is_sensitive_key(key) and isinstance(value, (str, int, float)):
                    token = self._token_for(self._category_from_key(key), str(value))
                    anonymized[key] = token
                    continue
                anonymized[key] = self.anonymize_structure(value)
            return anonymized

        if isinstance(payload, list):
            return [self.anonymize_structure(item) for item in payload]

        if isinstance(payload, str):
            return self.anonymize_text(payload)

        return payload

    def deanonymize_text(self, text: str) -> str:
        """Replace placeholders with original values."""
        if not self.enabled or not isinstance(text, str) or not text:
            return text

        restored = text
        for token, value in sorted(
            self._token_to_value.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            restored = restored.replace(token, value)
        return restored

    def deanonymize_structure(self, payload: Any) -> Any:
        """Recursively de-anonymize payload strings."""
        if not self.enabled:
            return payload

        if isinstance(payload, dict):
            return {key: self.deanonymize_structure(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self.deanonymize_structure(item) for item in payload]
        if isinstance(payload, str):
            return self.deanonymize_text(payload)
        return payload

    def contains_placeholders(self, text: str) -> bool:
        """Check whether a text still contains placeholder tokens."""
        if not isinstance(text, str):
            return False
        return bool(self._PLACEHOLDER_REGEX.search(text))

    def _token_for(self, category: str, value: str) -> str:
        clean_value = (value or "").strip()
        if not clean_value:
            return clean_value

        existing = self._value_to_token.get(clean_value)
        if existing:
            return existing

        self._category_counts[category] += 1
        token = f"[{category}_{self._category_counts[category]}]"
        self._value_to_token[clean_value] = token
        self._token_to_value[token] = clean_value
        return token

    def _replace_phone_match(self, value: str) -> str:
        if not self._is_valid_phone_candidate(value):
            return value
        return self._token_for("PHONE", value)

    @staticmethod
    def _is_valid_phone_candidate(value: str) -> bool:
        digits_count = sum(1 for char in value if char.isdigit())
        return digits_count >= 9

    def _is_sensitive_key(self, key: str) -> bool:
        key_lc = str(key or "").strip().lower()
        if key_lc == "id" or key_lc.endswith("_id") or key_lc == "employee_id":
            return True
        return any(keyword in key_lc for keyword in self._SENSITIVE_KEYWORDS)

    @staticmethod
    def _category_from_key(key: str) -> str:
        key_lc = str(key or "").strip().lower()
        if "email" in key_lc or "mail" in key_lc:
            return "EMAIL"
        if "phone" in key_lc or "telefono" in key_lc or "mobile" in key_lc:
            return "PHONE"
        if "name" in key_lc or "nombre" in key_lc:
            return "PERSON"
        if key_lc == "id" or key_lc.endswith("_id") or key_lc == "employee_id":
            return "ID"
        if "teams" in key_lc or "contact" in key_lc:
            return "CONTACT"
        return "VALUE"

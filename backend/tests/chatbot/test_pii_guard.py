"""
Unit tests for PIIGuard.
"""

import sys
from pathlib import Path

import pytest

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.chatbot.pii_guard import PIIGuard


@pytest.mark.unit
class TestPIIGuard:
    """Test suite for PIIGuard behavior."""

    def test_anonymize_text_replaces_direct_identifiers(self):
        guard = PIIGuard(enabled=True)
        text = "Contact me at ana@example.com or +34 612 345 678, employee EMP-1234"

        anonymized = guard.anonymize_text(text)

        assert "ana@example.com" not in anonymized
        assert "+34 612 345 678" not in anonymized
        assert "EMP-1234" not in anonymized
        assert "[EMAIL_1]" in anonymized
        assert "[PHONE_1]" in anonymized
        assert "[ID_1]" in anonymized

    def test_anonymize_structure_masks_sensitive_keys(self):
        guard = PIIGuard(enabled=True)
        payload = {
            "mentor": {
                "name": "Ana Perez",
                "email": "ana@example.com",
                "teams": "@ana.perez",
            },
            "notes": "Reach me at ana@example.com",
        }

        anonymized = guard.anonymize_structure(payload)

        assert anonymized["mentor"]["name"].startswith("[PERSON_")
        assert anonymized["mentor"]["email"].startswith("[EMAIL_")
        assert anonymized["mentor"]["teams"].startswith("[CONTACT_")
        assert "ana@example.com" not in anonymized["notes"]

    def test_anonymization_is_deterministic_per_value(self):
        guard = PIIGuard(enabled=True)
        text = "ana@example.com then again ana@example.com"

        anonymized = guard.anonymize_text(text)

        assert anonymized.count("[EMAIL_1]") == 2

    def test_deanonymize_structure_restores_original_values(self):
        guard = PIIGuard(enabled=True)
        payload = {
            "message": "Call me at +34 612 345 678",
            "email": "ana@example.com",
        }

        anonymized = guard.anonymize_structure(payload)
        restored = guard.deanonymize_structure(anonymized)

        assert restored == payload

    def test_has_unmasked_pii_text_detects_email_phone_id(self):
        guard = PIIGuard(enabled=True)

        assert guard.has_unmasked_pii_text("mail: x@y.com") is True
        assert guard.has_unmasked_pii_text("id EMP-999") is True
        assert guard.has_unmasked_pii_text("phone +34 699 123 456") is True

    def test_has_unmasked_pii_text_ignores_placeholders(self):
        guard = PIIGuard(enabled=True)
        text = "Contact [EMAIL_1] and [PHONE_1] for details"

        assert guard.has_unmasked_pii_text(text) is False

    def test_phone_detection_ignores_short_numeric_patterns(self):
        guard = PIIGuard(enabled=True)

        assert guard.has_unmasked_pii_text("Date 2025-01-01") is False
        assert guard.has_unmasked_pii_text("Code 123-45") is False

    def test_has_unmasked_pii_structure_checks_nested_payload(self):
        guard = PIIGuard(enabled=True)
        payload = {
            "prompt": "No pii here",
            "history": [
                {"role": "user", "content": "my email is one@example.com"},
            ],
        }

        assert guard.has_unmasked_pii_structure(payload) is True

        anonymized = guard.anonymize_structure(payload)
        assert guard.has_unmasked_pii_structure(anonymized) is False

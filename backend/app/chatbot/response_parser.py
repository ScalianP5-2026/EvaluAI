"""
Response Parser for EvaluAI Chatbot Core.

Parses Gemini responses and ensures JSON structure validity.
Implements fallback for malformed responses.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResponseParseError(Exception):
    """Raised when response parsing fails permanently."""
    pass


def parse_response(raw_response: str) -> Dict[str, Any]:
    """
    Parse LLM response and ensure valid structure.

    Strategy:
    1. Try direct JSON parsing
    2. If fails, attempt to extract JSON block
    3. If still fails, return fallback structure

    Args:
        raw_response: Raw text response from Gemini

    Returns:
        Parsed dict with guaranteed structure:
        {
            "success": bool,
            "message": str,
            "recommendations": {...},
            "insights": {...},
            "metadata": {...},
            "risk_alert": str or None,
            "raw": str (original response for debugging)
        }
    """
    if not raw_response or not raw_response.strip():
        logger.error("Empty response received from Gemini")
        return _fallback_response("Empty response from Gemini", raw_response)

    # Attempt 1: Direct JSON parsing
    try:
        parsed = json.loads(raw_response)
        logger.info("Response parsed as direct JSON")
        return _validate_and_wrap_response(parsed, raw_response)

    except json.JSONDecodeError as e:
        logger.warning(f"Direct JSON parsing failed: {e}")

    # Attempt 2: Extract JSON from response
    extracted_json = _extract_json_from_text(raw_response)
    if extracted_json:
        try:
            parsed = json.loads(extracted_json)
            logger.info("Response parsed after JSON extraction")
            return _validate_and_wrap_response(parsed, raw_response)
        except json.JSONDecodeError:
            logger.warning("Extracted JSON also failed to parse")

    # Attempt 3: Fallback
    logger.error("All parsing attempts failed. Using fallback response.")
    return _fallback_response(
        "Failed to parse LLM response. Using fallback structure.",
        raw_response
    )


def _extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON block from text that may contain extra characters.

    Args:
        text: Text potentially containing JSON

    Returns:
        JSON string or None if not found
    """
    # Look for JSON objects: { ... }
    # Try to find the first { and match closing }
    start_idx = text.find("{")
    if start_idx == -1:
        return None

    # Count braces to find matching closing
    brace_count = 0
    for i in range(start_idx, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                return text[start_idx : i + 1]

    return None


def _validate_and_wrap_response(
    parsed: Dict[str, Any],
    raw_response: str
) -> Dict[str, Any]:
    """
    Validate parsed response structure and wrap in standard format.

    Args:
        parsed: Parsed JSON dict from Gemini
        raw_response: Original raw response

    Returns:
        Standardized response dict
    """
    # Ensure required top-level keys
    required_keys = ["message", "recommendations", "insights"]
    
    has_all_required = all(key in parsed for key in required_keys)
    
    if not has_all_required:
        logger.warning(
            f"Parsed response missing required keys. "
            f"Found: {list(parsed.keys())}"
        )

    # Set defaults for missing optional fields
    if "metadata" not in parsed:
        parsed["metadata"] = {
            "goal_detected": False,
            "goal_clarity": "low",
            "recommended_skill": None,
        }

    if "risk_alert" not in parsed:
        parsed["risk_alert"] = None

    # Return wrapped response
    return {
        "success": True,
        "message": parsed.get("message", "No message"),
        "recommendations": parsed.get("recommendations", {}),
        "insights": parsed.get("insights", {}),
        "metadata": parsed.get("metadata", {}),
        "risk_alert": parsed.get("risk_alert"),
        "raw": raw_response,
    }


def _fallback_response(message: str, raw_response: str) -> Dict[str, Any]:
    """
    Generate fallback response when parsing fails.

    Args:
        message: Error message to include
        raw_response: Original raw response

    Returns:
        Safe fallback structure
    """
    return {
        "success": False,
        "message": f"[System Fallback] {message}. Original response: {raw_response[:100]}...",
        "recommendations": {
            "course": None,
            "mentor": None,
            "plan_30_days": [],
        },
        "insights": {
            "general": "Unable to parse chatbot response",
            "department": None,
            "personal": None,
        },
        "metadata": {
            "goal_detected": False,
            "goal_clarity": "low",
            "recommended_skill": None,
        },
        "risk_alert": "parse_error",
        "raw": raw_response,
    }


def validate_response_structure(response: Dict[str, Any]) -> bool:
    """
    Validate response has all required fields.

    Args:
        response: Parsed response dict

    Returns:
        True if valid, False otherwise
    """
    required = ["success", "message", "recommendations", "insights", "raw"]
    return all(key in response for key in required)

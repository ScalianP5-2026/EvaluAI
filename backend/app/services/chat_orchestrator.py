from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings
from app.services.recommender import create_chat_response

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are EvaluAI, an enterprise learning assistant for HR and L&D teams.
Return only valid JSON with this exact schema:
{
  "message": "string",
  "recommended_courses": ["string", "string", "string"],
  "recommended_mentor": "string",
  "thirty_day_plan": ["string", "string", "string", "string"],
  "similar_profile_improvement": 0.0
}

Rules:
- Keep recommendations practical and concise.
- Output 1 to 3 courses and exactly 4 plan steps.
- Similar profile improvement must be a number between 8 and 45.
- Do not include markdown or extra text outside JSON.
""".strip()


def _safe_float(value: Any, default: float = 20.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_json_payload(raw_content: str) -> dict[str, Any]:
    content = raw_content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response does not contain JSON object")

    return json.loads(content[start : end + 1])


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message", "")).strip() or (
        "Focus on practical learning cycles and weekly progress checks."
    )

    courses = []
    for item in payload.get("recommended_courses", []):
        text = str(item).strip()
        if text:
            courses.append(text)
    if not courses:
        courses = [
            "Python for Data Analysis (internal)",
            "Prompt Engineering Basics (internal)",
        ]
    courses = courses[:3]

    mentor = str(payload.get("recommended_mentor", "")).strip() or "No mentor match"

    plan = []
    for item in payload.get("thirty_day_plan", []):
        text = str(item).strip()
        if text:
            plan.append(text)

    if len(plan) < 4:
        plan = [
            "Days 1-7: complete selected modules and define practical use cases",
            "Days 8-15: build one role-aligned mini project with AI assistance",
            "Days 16-23: review progress with a mentor and close skill gaps",
            "Days 24-30: present outcomes and set your next learning objective",
        ]
    else:
        plan = plan[:4]

    improvement = _safe_float(payload.get("similar_profile_improvement"), 20.0)
    improvement = round(min(max(improvement, 8.0), 45.0), 1)

    return {
        "message": message,
        "recommended_courses": courses,
        "recommended_mentor": mentor,
        "thirty_day_plan": plan,
        "similar_profile_improvement": improvement,
    }


def _build_prompt_context(request, repository) -> str:
    surveys_df = repository.get_surveys()
    courses_df = repository.get_courses()
    mentors_df = repository.get_mentors()

    matching_courses = []
    if not courses_df.empty:
        for _, row in courses_df.head(8).iterrows():
            title = str(row.get("title", "Untitled course")).strip()
            tags = str(row.get("tags", "")).strip()
            if title:
                matching_courses.append(f"- {title} | tags: {tags}")

    mentor_catalog = []
    if not mentors_df.empty:
        for _, row in mentors_df.head(8).iterrows():
            mentor_name = str(row.get("mentor_name", "Unknown mentor")).strip()
            expertise = str(row.get("expertise", "")).strip()
            mentor_catalog.append(f"- {mentor_name} | expertise: {expertise}")

    role_avg = 0.0
    if not surveys_df.empty and "role" in surveys_df and "self_efficacy" in surveys_df:
        similar = surveys_df[surveys_df["role"].str.lower() == request.employee_role.lower()]
        if not similar.empty:
            role_avg = round(float(similar["self_efficacy"].mean()), 2)

    return "\n".join(
        [
            "Employee profile:",
            f"- role: {request.employee_role}",
            f"- learning_goal: {request.learning_goal}",
            f"- ai_usage: {request.ai_usage}",
            f"- self_efficacy: {request.self_efficacy}",
            f"- motivation: {request.motivation}",
            f"- avg_self_efficacy_in_role: {role_avg}",
            "",
            "Courses catalog sample:",
            *matching_courses,
            "",
            "Mentors catalog sample:",
            *mentor_catalog,
        ]
    )


def _create_foundry_chat_response(request, repository) -> dict[str, Any]:
    if not settings.azure_foundry_endpoint:
        raise RuntimeError("EVALUAI_AZURE_FOUNDRY_ENDPOINT is missing")
    if not settings.azure_foundry_api_key:
        raise RuntimeError("EVALUAI_AZURE_FOUNDRY_API_KEY is missing")
    if not settings.azure_foundry_model:
        raise RuntimeError("EVALUAI_AZURE_FOUNDRY_MODEL is missing")

    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "azure-ai-inference dependency is not installed"
        ) from exc

    client = ChatCompletionsClient(
        endpoint=settings.azure_foundry_endpoint,
        credential=AzureKeyCredential(settings.azure_foundry_api_key),
    )

    completion = client.complete(
        messages=[
            SystemMessage(content=SYSTEM_PROMPT),
            UserMessage(content=_build_prompt_context(request, repository)),
        ],
        model=settings.azure_foundry_model,
        temperature=settings.azure_foundry_temperature,
    )

    content = ""
    if completion.choices:
        message = completion.choices[0].message
        content = str(message.content) if message and message.content else ""

    payload = _parse_json_payload(content)
    return _normalize_payload(payload)


def create_chat_response_orchestrated(request, repository) -> dict[str, Any]:
    provider = settings.chat_provider.strip().lower()
    if provider in {"azure_foundry", "foundry", "azure"}:
        try:
            return _create_foundry_chat_response(request, repository)
        except Exception:
            logger.exception(
                "Azure Foundry chat failed; falling back to rule-based recommender"
            )

    return create_chat_response(request, repository)

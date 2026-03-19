from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 1
    }


def _recommend_courses(goal: str, courses_df, max_items: int = 3) -> list[str]:
    if courses_df.empty:
        return [
            "Python for Data Analysis (internal)",
            "Prompt Engineering Basics (internal)",
            "Machine Learning Foundations (internal)",
        ]

    goal_tokens = _tokenize(goal)
    ranked = []

    for _, row in courses_df.iterrows():
        tags = _tokenize(str(row.get("tags", "")))
        title = str(row.get("title", "Untitled course"))
        url = str(row.get("url", ""))

        overlap = len(goal_tokens.intersection(tags))
        ranked.append((overlap, f"{title} - {url}".strip(" -")))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [item[1] for item in ranked[:max_items]]
    if not any(score > 0 for score, _ in ranked[:max_items]):
        return [item[1] for item in ranked[:max_items]]
    return selected


def _recommend_mentor(goal: str, mentors_df) -> str:
    if mentors_df.empty:
        return "No mentor catalog available"

    goal_tokens = _tokenize(goal)
    best_name = "No mentor match"
    best_score = -1

    for _, row in mentors_df.iterrows():
        expertise_tokens = _tokenize(str(row.get("expertise", "")))
        score = len(goal_tokens.intersection(expertise_tokens))
        if score > best_score:
            best_score = score
            best_name = str(row.get("mentor_name", "Unknown mentor"))

    return best_name


def _estimate_improvement(surveys_df, role: str, ai_usage: str) -> float:
    if surveys_df.empty:
        return 20.0

    role_mask = surveys_df["role"].str.lower() == role.lower()
    usage_mask = surveys_df["ai_usage"].str.lower() == ai_usage.lower()
    similar = surveys_df[role_mask & usage_mask]

    if similar.empty:
        similar = surveys_df[surveys_df["role"].str.lower() == role.lower()]

    if similar.empty:
        return 20.0

    baseline = float(similar["self_efficacy"].mean())
    estimated = min(max(baseline / 10.0 * 25.0 + 8.0, 8.0), 45.0)
    return round(estimated, 1)


def create_chat_response(request, repository) -> dict[str, object]:
    surveys_df = repository.get_surveys()
    courses_df = repository.get_courses()
    mentors_df = repository.get_mentors()

    courses = _recommend_courses(request.learning_goal, courses_df)
    mentor = _recommend_mentor(request.learning_goal, mentors_df)
    improvement = _estimate_improvement(
        surveys_df,
        request.employee_role,
        request.ai_usage,
    )

    thirty_day_plan = [
        "Days 1-7: complete selected course modules and document 3 applied prompts",
        "Days 8-15: implement one mini project aligned to your current role",
        "Days 16-23: review progress with mentor and close two specific skill gaps",
        "Days 24-30: publish outcomes and define next learning objective",
    ]

    message = (
        f"For your goal '{request.learning_goal}', focus on short practical cycles. "
        f"With consistent execution, your profile could improve around "
        f"{improvement}% in self efficacy."
    )

    return {
        "message": message,
        "recommended_courses": courses,
        "recommended_mentor": mentor,
        "thirty_day_plan": thirty_day_plan,
        "similar_profile_improvement": improvement,
    }

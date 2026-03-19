from __future__ import annotations

import re

POSITIVE_WORDS = {
    "good",
    "better",
    "helpful",
    "improve",
    "confident",
    "clear",
    "motivated",
    "fast",
    "great",
    "useful",
}

NEGATIVE_WORDS = {
    "unclear",
    "slow",
    "bad",
    "difficult",
    "frustrated",
    "blocked",
    "lost",
    "confusing",
    "hard",
    "worse",
}

TOPIC_KEYWORDS = {
    "motivation": {"motivation", "engagement", "focus", "interested"},
    "tools": {"tool", "assistant", "chatgpt", "gemini", "copilot", "prompt"},
    "time": {"time", "hours", "schedule", "deadline", "quick"},
    "support": {"support", "mentor", "manager", "feedback", "help"},
    "difficulty": {"difficult", "hard", "complex", "overwhelmed", "confusing"},
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def analyze_comments(comments: list[str]) -> dict[str, object]:
    tokens = []
    for comment in comments:
        tokens.extend(_tokenize(comment))

    if not tokens:
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "topics": [],
            "group_recommendations": ["Collect more feedback to generate insights"],
        }

    positive_hits = sum(token in POSITIVE_WORDS for token in tokens)
    negative_hits = sum(token in NEGATIVE_WORDS for token in tokens)
    sentiment_score = round(
        (positive_hits - negative_hits) / max(len(tokens), 1),
        3,
    )

    if sentiment_score > 0.02:
        sentiment = "positive"
    elif sentiment_score < -0.02:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        matches = sum(token in keywords for token in tokens)
        topics.append({"topic": topic, "matches": matches})

    topics.sort(key=lambda item: item["matches"], reverse=True)

    recommendations = []
    if sentiment == "negative":
        recommendations.append("Run weekly office hours to remove immediate blockers")

    if any(topic["topic"] == "difficulty" and topic["matches"] > 0 for topic in topics):
        recommendations.append("Break content into shorter guided modules with examples")

    if any(topic["topic"] == "time" and topic["matches"] > 0 for topic in topics):
        recommendations.append("Add micro-learning sessions under 20 minutes")

    if any(topic["topic"] == "support" and topic["matches"] > 0 for topic in topics):
        recommendations.append("Pair learners with mentors based on role and goal")

    if not recommendations:
        recommendations.append(
            "Current feedback is stable. Keep personalized learning paths active"
        )

    return {
        "overall_sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "topics": topics,
        "group_recommendations": recommendations,
    }

from __future__ import annotations

AI_USAGE_SCORE = {
    "never": 0,
    "rarely": 1,
    "sometimes": 2,
    "frequently": 3,
    "always": 4,
}


def build_dashboard_summary(surveys_df):
    if surveys_df.empty:
        return {
            "total_employees": 0,
            "avg_motivation": 0.0,
            "avg_self_efficacy": 0.0,
            "avg_ai_use_score": 0.0,
            "usage_distribution": [
                {"level": level, "count": 0}
                for level in ("never", "rarely", "sometimes", "frequently", "always")
            ],
            "correlations": [],
            "insights": ["No survey data available yet"],
        }

    working = surveys_df.copy()
    working["ai_use_score"] = working["ai_usage"].map(AI_USAGE_SCORE).fillna(0)

    usage_distribution = [
        {
            "level": level,
            "count": int((working["ai_usage"] == level).sum()),
        }
        for level in ("never", "rarely", "sometimes", "frequently", "always")
    ]

    correlations = []
    correlation_fields = [
        ("motivation", "AI usage vs motivation"),
        ("talent_development", "AI usage vs talent development"),
        ("self_efficacy", "AI usage vs self efficacy"),
        ("experience_years", "AI usage vs experience"),
        ("acceptance", "AI usage vs acceptance"),
    ]
    for column, label in correlation_fields:
        if working[column].nunique() > 1 and working["ai_use_score"].nunique() > 1:
            corr_value = working[column].corr(working["ai_use_score"])
        else:
            corr_value = 0.0
        correlations.append(
            {
                "metric": label,
                "value": round(float(corr_value), 3),
            }
        )

    avg_ai_use = round(float(working["ai_use_score"].mean()), 2)
    avg_motivation = round(float(working["motivation"].mean()), 2)
    avg_self_efficacy = round(float(working["self_efficacy"].mean()), 2)

    insights = []
    if avg_ai_use < 1.5:
        insights.append(
            "AI adoption is low. Prioritize enablement and hands-on prompts."
        )
    else:
        insights.append(
            "AI adoption is moderate/high. Scale advanced use cases by role."
        )

    if avg_motivation >= 7:
        insights.append(
            "Motivation trend is strong. Keep personalized learning plans active."
        )
    else:
        insights.append(
            "Motivation is below target. Add manager follow-up and short learning goals."
        )

    if avg_self_efficacy >= 7:
        insights.append(
            "Self efficacy is solid. Promote peer mentoring to spread expertise."
        )
    else:
        insights.append(
            "Self efficacy needs support. Add guided paths and mentor checkpoints."
        )

    return {
        "total_employees": int(len(working)),
        "avg_motivation": avg_motivation,
        "avg_self_efficacy": avg_self_efficacy,
        "avg_ai_use_score": avg_ai_use,
        "usage_distribution": usage_distribution,
        "correlations": correlations,
        "insights": insights,
    }

from __future__ import annotations

import pandas as pd

AI_USAGE_SCORE = {
    "never": 0,
    "rarely": 1,
    "sometimes": 2,
    "frequently": 3,
    "always": 4,
}

AI_USAGE_LEVELS = ("never", "rarely", "sometimes", "frequently", "always")


def _safe_mean(dataframe, column: str) -> float:
    if column not in dataframe.columns:
        return 0.0
    numeric = pd.to_numeric(dataframe[column], errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return round(float(numeric.mean()), 2)


def _category_distribution(
    series: pd.Series,
    top_n: int | None = None,
) -> list[dict[str, int | str]]:
    cleaned = series.fillna("Sin dato").astype(str).str.strip()
    cleaned = cleaned.replace("", "Sin dato")
    counts = cleaned.value_counts()
    if top_n is not None:
        counts = counts.head(top_n)
    return [{"label": str(label), "count": int(count)} for label, count in counts.items()]


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "si"}


def build_dashboard_summary(surveys_df):
    if surveys_df.empty:
        return {
            "total_employees": 0,
            "avg_motivation": 0.0,
            "avg_self_efficacy": 0.0,
            "avg_ai_use_score": 0.0,
            "avg_age": 0.0,
            "avg_ai_integration": 0.0,
            "avg_human_preference": 0.0,
            "usage_distribution": [
                {"level": level, "count": 0}
                for level in AI_USAGE_LEVELS
            ],
            "gender_distribution": [],
            "department_distribution": [],
            "primary_tool_distribution": [],
            "ai_tools_usage": [],
            "correlations": [],
            "insights": ["No hay datos de encuestas disponibles"],
        }

    working = surveys_df.copy()
    working["ai_use_score"] = working["ai_usage"].map(AI_USAGE_SCORE).fillna(0)

    usage_distribution = [
        {
            "level": level,
            "count": int((working["ai_usage"] == level).sum()),
        }
        for level in AI_USAGE_LEVELS
    ]

    gender_distribution = (
        _category_distribution(working["genero"])
        if "genero" in working.columns
        else []
    )
    if "departamento" in working.columns:
        department_distribution = _category_distribution(working["departamento"], top_n=8)
    elif "role" in working.columns:
        department_distribution = _category_distribution(working["role"], top_n=8)
    else:
        department_distribution = []
    primary_tool_distribution = (
        _category_distribution(working["herramienta_principal"], top_n=8)
        if "herramienta_principal" in working.columns
        else []
    )

    tool_fields = [
        ("usa_chatgpt", "ChatGPT"),
        ("usa_gemini", "Gemini"),
        ("usa_copilot", "Copilot"),
        ("usa_lms_ia", "LMS con IA"),
        ("usa_otra_ia", "Otra IA"),
    ]
    ai_tools_usage = []
    for field, label in tool_fields:
        if field not in working.columns:
            continue
        count = int(working[field].apply(_as_bool).sum())
        ai_tools_usage.append({"label": label, "count": count})

    correlations = []
    correlation_fields = [
        ("motivation", "frecuencia_uso_ia vs motivacion_promedio"),
        ("talent_development", "frecuencia_uso_ia vs desarrollo_talento_promedio"),
        ("self_efficacy", "frecuencia_uso_ia vs autoeficacia_promedio"),
        ("experience_years", "frecuencia_uso_ia vs antiguedad_empresa"),
        ("acceptance", "frecuencia_uso_ia vs aceptacion_promedio"),
    ]
    for column, label in correlation_fields:
        if working[column].nunique() > 1 and working["ai_use_score"].nunique() > 1:
            corr_value = working[column].corr(working["ai_use_score"])
        else:
            corr_value = 0.0
        correlations.append({"metric": label, "value": round(float(corr_value), 3)})

    avg_ai_use = round(float(working["ai_use_score"].mean()), 2)
    avg_motivation = _safe_mean(working, "motivation")
    avg_self_efficacy = _safe_mean(working, "self_efficacy")
    avg_age = _safe_mean(working, "edad")
    avg_ai_integration = _safe_mean(working, "nivel_integracion_ia")
    avg_human_preference = _safe_mean(working, "prefiere_humano_vs_ia")

    insights = []
    if avg_ai_use < 1.5:
        insights.append(
            "La adopcion de IA es baja. Prioriza capacitacion y casos practicos."
        )
    else:
        insights.append(
            "La adopcion de IA es moderada/alta. Escala casos avanzados por rol."
        )

    if avg_motivation >= 7:
        insights.append(
            "La motivacion es alta. Mantener planes de aprendizaje personalizados."
        )
    else:
        insights.append(
            "La motivacion esta por debajo del objetivo. Reforzar seguimiento y metas cortas."
        )

    if avg_self_efficacy >= 7:
        insights.append("La autoeficacia es solida. Promover mentoring entre pares.")
    else:
        insights.append(
            "La autoeficacia necesita refuerzo. Anadir rutas guiadas y checkpoints con mentor."
        )

    if avg_ai_integration >= 4.0:
        insights.append(
            "La integracion de IA en el aprendizaje diario es alta. Enfocar en practicas avanzadas."
        )
    else:
        insights.append(
            "La integracion de IA aun es moderada. Reforzar casos practicos por departamento."
        )

    return {
        "total_employees": int(len(working)),
        "avg_motivation": avg_motivation,
        "avg_self_efficacy": avg_self_efficacy,
        "avg_ai_use_score": avg_ai_use,
        "avg_age": avg_age,
        "avg_ai_integration": avg_ai_integration,
        "avg_human_preference": avg_human_preference,
        "usage_distribution": usage_distribution,
        "gender_distribution": gender_distribution,
        "department_distribution": department_distribution,
        "primary_tool_distribution": primary_tool_distribution,
        "ai_tools_usage": ai_tools_usage,
        "correlations": correlations,
        "insights": insights,
    }

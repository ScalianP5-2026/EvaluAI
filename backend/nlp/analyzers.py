"""Rule-based NLP analyzers for sentiment, topics, and dependency scoring.

All analyzers work on plain text without external ML packages.
They produce the same column names that the legacy CSV-based pipeline
used so the downstream aggregation in ``service.py`` needs no changes.

v2 improvements:
- Expanded keyword taxonomy + n-gram matching to reduce no_topic rate
- topic_probability replaced with topic_relevance (same field name for compat)
- Added motivation_proxy from M1-M4 Likert scores
- Recalibrated topic risk scoring
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

# ═══════════════════════════════════════════════════════════════
# BILINGUAL SENTIMENT WORD LISTS
# ═══════════════════════════════════════════════════════════════

POSITIVE_WORDS = {
    # Spanish
    "bueno", "buena", "bien", "mejor", "excelente", "positivo", "positiva",
    "útil", "fácil", "rápido", "rápida", "claro", "clara", "motivado",
    "motivada", "interesante", "eficaz", "ayuda", "aprendizaje", "progreso",
    "confianza", "seguridad", "satisfecho", "satisfecha", "cómodo", "cómoda",
    "productivo", "productiva", "avance", "mejorar", "facilita", "valioso",
    "valiosa", "genial", "práctico", "práctica", "innovador", "innovadora",
    "estimulante", "accesible", "intuitivo", "intuitiva", "recomiendo",
    "enriquecedor", "enriquecedora", "beneficioso", "beneficiosa",
    "agradable", "óptimo", "óptima", "adecuado", "adecuada",
    "favorable", "provechoso", "provechosa", "fluido", "fluida",
    "gratificante", "oportuno", "oportuna", "eficiente",
    # English
    "good", "great", "better", "helpful", "improve", "confident", "clear",
    "motivated", "fast", "useful", "easy", "excellent", "positive",
    "effective", "productive", "satisfied", "comfortable", "practical",
    "innovative", "intuitive", "valuable", "progress", "recommend",
    "beneficial", "rewarding", "enriching", "adequate", "optimal",
}

NEGATIVE_WORDS = {
    # Spanish
    "malo", "mala", "peor", "difícil", "complejo", "compleja", "confuso",
    "confusa", "lento", "lenta", "frustrante", "frustrado", "frustrada",
    "bloqueado", "bloqueada", "perdido", "perdida", "complicado", "complicada",
    "problema", "problemas", "barrera", "barreras", "dificultad", "dificultades",
    "inseguro", "insegura", "estresante", "abrumado", "abrumada",
    "desmotivado", "desmotivada", "ineficaz", "imposible",
    "incómodo", "incómoda", "negativo", "negativa", "falta",
    "insuficiente", "inadecuado", "inadecuada", "limitado", "limitada",
    "tedioso", "tediosa", "aburrido", "aburrida", "repetitivo", "repetitiva",
    "confusión", "desconfianza", "inútil", "innecesario", "innecesaria",
    # English
    "bad", "worse", "difficult", "complex", "confusing", "slow",
    "frustrated", "blocked", "lost", "hard", "problem", "barrier",
    "unclear", "stressful", "overwhelming", "demotivated", "ineffective",
    "impossible", "uncomfortable", "negative", "lacking", "insufficient",
    "inadequate", "boring", "tedious", "useless",
}

# ═══════════════════════════════════════════════════════════════
# BILINGUAL TOPIC KEYWORD TAXONOMY (expanded v2)
# ═══════════════════════════════════════════════════════════════
# Each topic has single-word keywords plus multi-word phrases (bigrams)
# that are matched separately after tokenization.

TOPIC_KEYWORDS: dict[str, set[str]] = {
    "tools_and_platforms": {
        "chatgpt", "gemini", "copilot", "herramienta", "herramientas",
        "plataforma", "plataformas", "lms", "tool", "tools", "platform",
        "software", "aplicación", "app", "tecnología", "technology",
        "ia", "ai", "inteligencia", "artificial", "digital", "digitales",
        "programa", "programas", "sistema", "sistemas", "robot", "bot",
        "automatización", "automático", "automática",
    },
    "learning_experience": {
        "aprendizaje", "curso", "cursos", "formación", "capacitación",
        "learning", "training", "course", "educación", "enseñanza",
        "módulo", "módulos", "contenido", "material", "sesión", "sesiones",
        "clase", "clases", "lección", "lecciones", "práctica", "ejercicio",
        "ejercicios", "taller", "talleres", "ejemplo", "ejemplos",
        "recurso", "recursos", "teoría", "teórico", "teórica",
        "didáctico", "didáctica", "pedagógico", "pedagógica",
    },
    "time_and_workload": {
        "tiempo", "carga", "horas", "horario", "deadline", "rápido",
        "lento", "ritmo", "prisa", "urgente", "plazo", "duración",
        "time", "hours", "schedule", "workload", "pace",
        "disponibilidad", "dedicación", "intensivo", "intensiva",
        "corto", "largo", "breve", "extenso", "extensa",
    },
    "motivation_and_engagement": {
        "motivación", "interés", "estimulante", "engagement", "entusiasmo",
        "ganas", "ánimo", "ilusión", "inspiración", "compromiso",
        "motivation", "interest", "enthusiasm", "inspiring",
        "curiosidad", "voluntad", "impulso", "proactivo", "proactiva",
        "participación", "involucrado", "involucrada", "implicación",
    },
    "difficulty_and_barriers": {
        "difícil", "complejo", "barrera", "confuso", "problema",
        "obstáculo", "dificultad", "complicado", "error", "fallo",
        "difficult", "complex", "barrier", "confusing", "problem",
        "obstacle", "challenge", "challenging", "struggle",
        "reto", "retos", "limitación", "limitaciones", "fricción",
        "frustración", "incomprensible", "exigente",
    },
    "mentoring_and_support": {
        "mentor", "tutor", "apoyo", "feedback", "ayuda", "guía",
        "acompañamiento", "soporte", "orientación", "supervisión",
        "mentoring", "support", "help", "guidance", "coaching",
        "asesoramiento", "consulta", "consejo", "referencia",
        "compañero", "compañera", "equipo", "colaboración",
    },
    "autonomy_and_dependency": {
        "autónomo", "autónoma", "autonomía", "dependencia", "dependiente",
        "verificar", "criterio", "crítico", "crítica", "independiente",
        "autonomous", "autonomy", "dependency", "dependent", "independent",
        "critical", "thinking", "verify", "judgment",
        "confianza", "propio", "propia", "decisión", "decisiones",
        "capacidad", "seguridad", "responsabilidad",
    },
    "impact_and_value": {
        "impacto", "valor", "mejora", "competencia", "competencias",
        "resultado", "resultados", "beneficio", "rendimiento", "calidad",
        "impact", "value", "improvement", "competence", "result",
        "benefit", "performance", "quality", "outcome",
        "productividad", "eficiencia", "desarrollo", "crecimiento",
        "utilidad", "aplicabilidad", "transformación", "cambio",
    },
}

# Multi-word phrases that match as a unit (lowercased).
# These are checked by searching in the lowercased full text.
TOPIC_PHRASES: dict[str, list[str]] = {
    "tools_and_platforms": [
        "inteligencia artificial", "ia generativa",
        "machine learning", "deep learning",
    ],
    "learning_experience": [
        "experiencia de aprendizaje", "proceso de formación",
        "material didáctico", "plan de estudios",
    ],
    "time_and_workload": [
        "carga de trabajo", "falta de tiempo", "gestión del tiempo",
    ],
    "difficulty_and_barriers": [
        "curva de aprendizaje", "falta de conocimiento",
        "brecha digital", "falta de experiencia",
    ],
    "mentoring_and_support": [
        "trabajo en equipo", "sesión de apoyo",
    ],
    "autonomy_and_dependency": [
        "pensamiento crítico", "toma de decisiones",
        "sin verificar", "criterio propio",
    ],
}

# ═══════════════════════════════════════════════════════════════
# TOKENIZER
# ═══════════════════════════════════════════════════════════════


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenization that keeps accented characters and digits."""
    return re.findall(r"[a-záéíóúüñ0-9]+", text.lower())


# ═══════════════════════════════════════════════════════════════
# SENTIMENT ANALYZER
# ═══════════════════════════════════════════════════════════════


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Return rule-based sentiment for a single text fragment.

    Returns:
        dict with ``sentiment_label`` (positive / negative / neutral),
        ``sentiment_score`` (float in [-1, 1]), and
        ``sentiment_confidence`` (float in [0, 1]).
    """
    if not text or not text.strip():
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "sentiment_confidence": 0.0,
        }

    tokens = _tokenize(text)
    if not tokens:
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "sentiment_confidence": 0.0,
        }

    pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    total_signal = pos_hits + neg_hits

    score = (pos_hits - neg_hits) / max(len(tokens), 1)
    score = max(-1.0, min(1.0, round(score, 4)))

    confidence = min(1.0, round(total_signal / max(len(tokens), 1), 4))

    if score > 0.02:
        label = "positive"
    elif score < -0.02:
        label = "negative"
    else:
        label = "neutral"

    return {
        "sentiment_label": label,
        "sentiment_score": score,
        "sentiment_confidence": confidence,
    }


# ═══════════════════════════════════════════════════════════════
# TOPIC EXTRACTOR (v2 — keywords + phrases)
# ═══════════════════════════════════════════════════════════════


def extract_topics(text: str, top_n: int = 3) -> list[dict[str, Any]]:
    """Return top-N topic matches for a text fragment.

    Matches both single-word keywords and multi-word phrases.
    ``topic_probability`` is a relevance score (0-1) based on the
    fraction of the topic's keyword set that appeared, NOT a
    probabilistic model output.

    Each entry: ``{"topic_id": str, "matches": int, "topic_probability": float}``
    """
    if not text or not text.strip():
        return []

    tokens = _tokenize(text)
    if not tokens:
        return []

    text_lower = text.lower()

    scored: list[dict[str, Any]] = []
    for topic_id, keywords in TOPIC_KEYWORDS.items():
        # Count single-word keyword hits
        word_matches = sum(1 for t in tokens if t in keywords)

        # Count multi-word phrase hits
        phrase_matches = 0
        phrases = TOPIC_PHRASES.get(topic_id, [])
        for phrase in phrases:
            if phrase in text_lower:
                phrase_matches += 1

        total_matches = word_matches + phrase_matches * 2  # phrases count double

        if total_matches > 0:
            # topic_probability = relevance = how much of the topic's
            # vocabulary appeared, capped at 1.0
            vocab_size = len(keywords) + len(phrases)
            relevance = min(1.0, round(total_matches / max(vocab_size * 0.3, 1), 4))
            scored.append({
                "topic_id": topic_id,
                "matches": total_matches,
                "topic_probability": relevance,
            })

    scored.sort(key=lambda x: x["matches"], reverse=True)
    return scored[:top_n]


# ═══════════════════════════════════════════════════════════════
# AI DEPENDENCY INDEX (from Likert C1-C4)
# ═══════════════════════════════════════════════════════════════


def compute_dependency_index(
    c1: float | None,
    c2: float | None,
    c3: float | None,
    c4: float | None,
) -> dict[str, Any]:
    """Compute AI autonomy/dependency index from C1-C4 Likert items.

    C1 (confío sin verificar)  — higher = more dependent  → positive weight
    C2 (difícil sin IA)        — higher = more dependent  → positive weight
    C3 (pensamiento crítico)   — higher = more autonomous → negative weight (inverted)
    C4 (reflexiono calidad)    — higher = more autonomous → negative weight (inverted)

    Index range:  approximately 0 (fully autonomous) to 1 (fully dependent).
    Category: low / medium / high
    """
    values = [c1, c2, c3, c4]
    valid = [v for v in values if v is not None and not pd.isna(v)]
    if not valid:
        return {
            "ai_autonomy_dependency_index": None,
            "ai_autonomy_dependency_category": "unknown",
        }

    # Safe defaults for missing items
    c1_val = float(c1) if c1 is not None and not pd.isna(c1) else 3.0
    c2_val = float(c2) if c2 is not None and not pd.isna(c2) else 3.0
    c3_val = float(c3) if c3 is not None and not pd.isna(c3) else 3.0
    c4_val = float(c4) if c4 is not None and not pd.isna(c4) else 3.0

    # Normalize each to 0-1 (assuming 1-5 Likert scale)
    dep_signal = ((c1_val - 1) / 4 + (c2_val - 1) / 4) / 2
    auto_signal = ((c3_val - 1) / 4 + (c4_val - 1) / 4) / 2

    # Index = dependency signal weighted against autonomy signal
    index = round(dep_signal * 0.6 + (1 - auto_signal) * 0.4, 4)
    index = max(0.0, min(1.0, index))

    if index > 0.66:
        category = "high"
    elif index >= 0.33:
        category = "medium"
    else:
        category = "low"

    return {
        "ai_autonomy_dependency_index": index,
        "ai_autonomy_dependency_category": category,
    }


# ═══════════════════════════════════════════════════════════════
# TOPIC RISK SCORE (v2 — recalibrated)
# ═══════════════════════════════════════════════════════════════

# Topics that inherently carry higher strategic risk weight.
_HIGH_RISK_TOPICS = {
    "difficulty_and_barriers",
    "autonomy_and_dependency",
    "time_and_workload",
}


def compute_topic_risk_score(
    sentiment_score: float,
    dependency_index: float | None,
    topic_id: str = "",
) -> float:
    """Combine sentiment, dependency, and topic type into a risk score [0, 1].

    v2 improvements:
    - Neutral sentiment now contributes mild risk (not zero)
    - Topic type modulates risk (difficulty/autonomy topics inherently riskier)
    - Better spread across the 0-1 range
    """
    dep = dependency_index if dependency_index is not None else 0.5

    # Sentiment risk: negative = high, neutral = mild, positive = low
    if sentiment_score < -0.02:
        sentiment_risk = 0.5 + min(0.5, abs(sentiment_score) * 2)
    elif sentiment_score > 0.02:
        sentiment_risk = max(0.0, 0.2 - sentiment_score * 0.5)
    else:
        sentiment_risk = 0.3  # neutral is not "no risk"

    # Topic type bonus: difficulty/autonomy/time topics are inherently riskier
    topic_bonus = 0.15 if topic_id in _HIGH_RISK_TOPICS else 0.0

    # Combine: 30% sentiment + 50% dependency + 20% topic type
    raw = sentiment_risk * 0.3 + dep * 0.5 + topic_bonus + 0.05
    return round(max(0.0, min(1.0, raw)), 4)


# ═══════════════════════════════════════════════════════════════
# AUTONOMY SIGNAL SCORE
# ═══════════════════════════════════════════════════════════════


def compute_autonomy_signal(
    c3: float | None,
    c4: float | None,
) -> float:
    """Autonomy signal from C3 (pensamiento crítico) + C4 (reflexiono calidad)."""
    vals = [v for v in [c3, c4] if v is not None and not pd.isna(v)]
    if not vals:
        return 0.5
    avg = sum(float(v) for v in vals) / len(vals)
    return round((avg - 1) / 4, 4)  # normalize 1-5 to 0-1


# ═══════════════════════════════════════════════════════════════
# MOTIVATION PROXY (from Likert M1-M4)
# ═══════════════════════════════════════════════════════════════


def compute_motivation_proxy(
    m1: float | None,
    m2: float | None,
    m3: float | None,
    m4: float | None,
) -> float:
    """Compute motivation proxy from M1-M4 Likert items.

    M1 (estimulante), M2 (aumenta interés), M3 (aporta valor),
    M4 (mayor esfuerzo) — all on 1-5 Likert scale.

    Returns normalized 0-1 score (average of available items).
    """
    vals = [v for v in [m1, m2, m3, m4] if v is not None and not pd.isna(v)]
    if not vals:
        return 0.5  # neutral default
    avg = sum(float(v) for v in vals) / len(vals)
    return round((avg - 1) / 4, 4)  # normalize 1-5 to 0-1


# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE (rule-based)
# ═══════════════════════════════════════════════════════════════

_RECOMMENDATION_RULES: list[tuple[str, str]] = [
    # (condition_key, recommendation_text)
    # Conditions are evaluated per-row after enrichment
]


def generate_recommendations(row: dict[str, Any]) -> list[str]:
    """Generate actionable recommendations for a single employee row."""
    recs: list[str] = []
    sent = str(row.get("sentiment_label", "")).lower()
    topic = str(row.get("topic_id", "")).lower()
    dep_cat = str(row.get("ai_autonomy_dependency_category", "")).lower()
    dep_idx = row.get("ai_autonomy_dependency_index")
    mot = row.get("delta_motivation_score")
    risk = row.get("topic_risk_score", 0)

    # High dependency + low critical thinking
    if dep_cat == "high":
        recs.append("Activar programa de mentoría en pensamiento crítico")

    # Negative sentiment + difficulty topic
    if sent == "negative" and topic in ("difficulty_and_barriers", "no_topic"):
        recs.append("Proporcionar sesiones de apoyo guiado con IA")

    # Negative sentiment overall
    if sent == "negative" and topic != "difficulty_and_barriers":
        recs.append("Realizar entrevista de seguimiento individual")

    # High risk score
    if risk is not None and float(risk) > 0.65:
        recs.append("Incluir en cohorte de intervención prioritaria")

    # Low motivation
    if mot is not None and float(mot) < 0.35:
        recs.append("Integrar en programa de engagement y motivación")

    # Time/workload pressure
    if topic == "time_and_workload":
        recs.append("Implementar micro-learning sessions (< 20 min)")

    # Mentoring needs
    if topic == "mentoring_and_support" and sent != "positive":
        recs.append("Asignar mentor especializado")

    # Positive + tools topic → advance
    if sent == "positive" and topic == "tools_and_platforms":
        recs.append("Continuar capacitación avanzada en herramientas IA")

    # Positive + learning → mentoring others
    if sent == "positive" and topic == "learning_experience":
        recs.append("Explorar rol como mentor para compañeros")

    # Medium dependency → coaching
    if dep_cat == "medium":
        recs.append("Sesiones de coaching en autonomía digital")

    # Autonomy topic + positive → recognize
    if topic == "autonomy_and_dependency" and sent == "positive":
        recs.append("Reconocer como referente en pensamiento crítico")

    return recs if recs else ["Mantener seguimiento regular"]


# ═══════════════════════════════════════════════════════════════
# ALERT FLAGS (rule-based)
# ═══════════════════════════════════════════════════════════════

# Alert category definitions
_ALERT_CATEGORIES = {
    "high_dependency": {"icon": "🔴", "severity": "high"},
    "negative_sentiment": {"icon": "🟡", "severity": "medium"},
    "difficulty_barriers": {"icon": "🟠", "severity": "medium"},
    "mentoring_needs": {"icon": "🔵", "severity": "low"},
    "time_pressure": {"icon": "⏰", "severity": "medium"},
    "low_motivation": {"icon": "📉", "severity": "high"},
}


def generate_alert_flags(row: dict[str, Any]) -> list[str]:
    """Return list of alert category keys triggered for this employee."""
    flags: list[str] = []
    sent = str(row.get("sentiment_label", "")).lower()
    topic = str(row.get("topic_id", "")).lower()
    dep_cat = str(row.get("ai_autonomy_dependency_category", "")).lower()
    mot = row.get("delta_motivation_score")
    risk = row.get("topic_risk_score", 0)

    if dep_cat == "high":
        flags.append("high_dependency")
    if sent == "negative":
        flags.append("negative_sentiment")
    if topic == "difficulty_and_barriers":
        flags.append("difficulty_barriers")
    if topic == "mentoring_and_support" and sent != "positive":
        flags.append("mentoring_needs")
    if topic == "time_and_workload":
        flags.append("time_pressure")
    if mot is not None and float(mot) < 0.35:
        flags.append("low_motivation")

    return flags


# ═══════════════════════════════════════════════════════════════
# ENRICH DATAFRAME (main entry point)
# ═══════════════════════════════════════════════════════════════


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add NLP columns to a raw survey_responses DataFrame.

    Produces:
      sentiment_label, sentiment_score, sentiment_confidence,
      topic_id, topic_probability, topic_risk_score,
      autonomy_signal_score, delta_motivation_score,
      ai_autonomy_dependency_index, ai_autonomy_dependency_category,
      full_text, recommendations, alert_flags
    """
    enriched = df.copy()

    # Build full_text from the two open-text fields
    col_pos = "open_positive_experience"
    col_neg = "open_difficulties_and_training_needs"

    def _concat_text(row: pd.Series) -> str:
        parts = []
        for col in [col_pos, col_neg]:
            val = row.get(col)
            if val is not None and not pd.isna(val) and str(val).strip():
                parts.append(str(val).strip())
        return " ".join(parts)

    enriched["full_text"] = enriched.apply(_concat_text, axis=1)

    # Sentiment
    sentiments = enriched["full_text"].apply(analyze_sentiment)
    enriched["sentiment_label"] = sentiments.apply(lambda s: s["sentiment_label"])
    enriched["sentiment_score"] = sentiments.apply(lambda s: s["sentiment_score"])
    enriched["sentiment_confidence"] = sentiments.apply(lambda s: s["sentiment_confidence"])

    # Topics — pick the top-1 topic as "topic_id"
    topics = enriched["full_text"].apply(lambda t: extract_topics(t, top_n=1))
    enriched["topic_id"] = topics.apply(
        lambda t: t[0]["topic_id"] if t else "no_topic"
    )
    enriched["topic_probability"] = topics.apply(
        lambda t: t[0]["topic_probability"] if t else 0.0
    )

    # Dependency index
    dep_results = enriched.apply(
        lambda row: compute_dependency_index(
            row.get("c1_confio_sin_verificar"),
            row.get("c2_dificil_sin_ia"),
            row.get("c3_pensamiento_critico"),
            row.get("c4_reflexiono_calidad"),
        ),
        axis=1,
    )
    enriched["ai_autonomy_dependency_index"] = dep_results.apply(
        lambda d: d["ai_autonomy_dependency_index"]
    )
    enriched["ai_autonomy_dependency_category"] = dep_results.apply(
        lambda d: d["ai_autonomy_dependency_category"]
    )

    # Autonomy signal
    enriched["autonomy_signal_score"] = enriched.apply(
        lambda row: compute_autonomy_signal(
            row.get("c3_pensamiento_critico"),
            row.get("c4_reflexiono_calidad"),
        ),
        axis=1,
    )

    # Motivation proxy (from M1-M4 Likert scores)
    enriched["delta_motivation_score"] = enriched.apply(
        lambda row: compute_motivation_proxy(
            row.get("m1_estimulante"),
            row.get("m2_aumenta_interes"),
            row.get("m3_aporta_valor"),
            row.get("m4_mayor_esfuerzo"),
        ),
        axis=1,
    )

    # Topic risk score (uses topic_id for risk modulation)
    enriched["topic_risk_score"] = enriched.apply(
        lambda row: compute_topic_risk_score(
            row.get("sentiment_score", 0.0),
            row.get("ai_autonomy_dependency_index"),
            row.get("topic_id", ""),
        ),
        axis=1,
    )

    # Recommendations (rule-based per row)
    enriched["recommendations"] = enriched.apply(
        lambda row: generate_recommendations(row.to_dict()), axis=1,
    )

    # Alert flags (rule-based per row)
    enriched["alert_flags"] = enriched.apply(
        lambda row: generate_alert_flags(row.to_dict()), axis=1,
    )

    return enriched


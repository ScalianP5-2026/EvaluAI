"""
Hybrid RAG orchestration for employee-personalized learning advice.

Design:
- Structured retrieval from Supabase (employee-aware catalog + mentor tables)
- File RAG retrieval from local CSV knowledge sources
- Ranking layer with weighted scoring and explainable reasons
- Tool-style orchestration trace for observability
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set

from .data_manager import DataManager


TOKEN_RE = re.compile(r"[a-zA-Z0-9_+\-]{2,}")


def _tokenize(text: str) -> Set[str]:
    return {match.group(0).lower() for match in TOKEN_RE.finditer(text or "")}


def _jaccard(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    inter = len(left & right)
    union = len(left | right)
    return inter / union if union else 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_ratio(value: Any, default: float = 0.5) -> float:
    ratio = _safe_float(value, default)
    if ratio > 1.0:
        ratio = ratio / 100.0
    return max(0.0, min(1.0, ratio))


def _parse_weekly_hours(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").lower()
    match = re.search(r"(\d+)", text)
    if not match:
        return 0.0
    return float(match.group(1))


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def _is_code_like_name(name: str) -> bool:
    """
    Detect short uppercase ID-like mentor names such as CDO, JJO, MLS.
    """
    cleaned = (name or "").strip()
    if not cleaned:
        return False
    return bool(re.fullmatch(r"[A-ZÁÉÍÓÚÑ]{2,5}", cleaned))


@dataclass
class Candidate:
    item_type: str
    title: str
    description: str
    source: str
    metadata: Dict[str, Any]
    score: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.item_type,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "metadata": self.metadata,
            "score": round(self.score, 4),
            "score_breakdown": self.breakdown,
            "reasons": self.reasons,
        }


class HybridRAGOrchestrator:
    """
    Implements a hybrid retrieval pipeline for educational advice.
    """

    _file_cache: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.data_root = Path(__file__).resolve().parents[2] / "data"

    def run(
        self,
        user_message: str,
        employee_ctx: Dict[str, Any],
        top_k_courses: int = 5,
        top_k_mentors: int = 3,
    ) -> Dict[str, Any]:
        query_tokens = _tokenize(user_message)
        inferred_skills = self._infer_skills(user_message)
        skill_tokens = _tokenize(" ".join(inferred_skills))
        previous_titles = self._load_previous_recommendations(employee_ctx)

        tool_trace: List[Dict[str, Any]] = []

        supabase_courses = self.dm.get_course_catalog(limit=250)
        supabase_mentors = self.dm.get_mentor_catalog(limit=250)
        tool_trace.append(
            {
                "tool": "structured_catalog_lookup",
                "courses_loaded": len(supabase_courses),
                "mentors_loaded": len(supabase_mentors),
            }
        )

        file_courses = self._load_file_course_docs()
        file_mentors = self._load_file_mentor_docs() + self._load_readable_mentor_profiles()
        tool_trace.append(
            {
                "tool": "file_knowledge_retrieval",
                "courses_loaded": len(file_courses),
                "mentors_loaded": len(file_mentors),
            }
        )

        course_candidates = self._build_course_candidates(supabase_courses, file_courses)
        mentor_candidates = self._build_mentor_candidates(supabase_mentors, file_mentors)

        ranked_courses = self._rank_courses(
            candidates=course_candidates,
            query_tokens=query_tokens,
            skill_tokens=skill_tokens,
            employee_ctx=employee_ctx,
            previous_titles=previous_titles,
            top_k=top_k_courses,
        )
        ranked_mentors = self._rank_mentors(
            candidates=mentor_candidates,
            query_tokens=query_tokens,
            skill_tokens=skill_tokens,
            employee_ctx=employee_ctx,
            top_k=top_k_mentors,
        )
        tool_trace.append(
            {
                "tool": "ranking_engine",
                "course_candidates": len(course_candidates),
                "mentor_candidates": len(mentor_candidates),
                "top_courses": len(ranked_courses),
                "top_mentors": len(ranked_mentors),
            }
        )

        evaluation = self._build_evaluation_snapshot(
            query_tokens=query_tokens,
            ranked_courses=ranked_courses,
            ranked_mentors=ranked_mentors,
        )

        return {
            "query_understanding": {
                "tokens": sorted(query_tokens)[:20],
                "inferred_skills": inferred_skills,
            },
            "ranked_courses": [candidate.to_dict() for candidate in ranked_courses],
            "ranked_mentors": [candidate.to_dict() for candidate in ranked_mentors],
            "recommended_programs": [candidate.to_dict() for candidate in ranked_courses[:3]],
            "tool_trace": tool_trace,
            "evaluation": evaluation,
            "citations": [
                {"title": candidate.title, "source": candidate.source}
                for candidate in ranked_courses[:5] + ranked_mentors[:3]
            ],
        }

    def _infer_skills(self, user_message: str) -> List[str]:
        text = (user_message or "").lower()
        skills = []
        hints = {
            "machine learning": ["machine learning", "ml", "model", "regression", "classification"],
            "nlp": ["nlp", "transformers", "llm", "prompt", "genai"],
            "python": ["python", "pandas", "numpy"],
            "data engineering": ["etl", "spark", "kafka", "data pipeline", "big data"],
            "cloud": ["azure", "aws", "gcp", "cloud"],
            "devops": ["docker", "kubernetes", "ci/cd", "devops"],
            "analytics": ["analytics", "power bi", "dashboard", "visualization"],
        }
        for skill, markers in hints.items():
            if any(marker in text for marker in markers):
                skills.append(skill)
        return skills

    def _load_previous_recommendations(self, employee_ctx: Dict[str, Any]) -> Set[str]:
        full_profile = employee_ctx.get("employee_full_profile", {}) or {}
        rows = full_profile.get("recommendation_events", []) or []
        titles = set()
        for row in rows:
            title = _normalize_title(str(row.get("course_recommended", "")))
            if title:
                titles.add(title)
        return titles

    def _load_file_course_docs(self) -> List[Dict[str, Any]]:
        cache_key = "file_courses"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        rows: List[Dict[str, Any]] = []
        path = self.data_root / "raw" / "programas_formacion.csv"
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    rows.append(
                        {
                            "title": row.get("nombre", ""),
                            "department": row.get("categoria", ""),
                            "skill_level": row.get("nivel", ""),
                            "description": row.get("descripcion", ""),
                            "technologies": row.get("tecnologias", ""),
                            "duration_hours": row.get("duracion_horas", ""),
                            "source": "file:programas_formacion.csv",
                        }
                    )
        self._file_cache[cache_key] = rows
        return rows

    def _load_file_mentor_docs(self) -> List[Dict[str, Any]]:
        cache_key = "file_mentors"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        rows: List[Dict[str, Any]] = []
        path = self.data_root / "raw" / "mentores.csv"
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    rows.append(
                        {
                            "mentor_id": row.get("id_mentor", ""),
                            "nombre": row.get("nombre", ""),
                            "especialidades": row.get("especialidades", ""),
                            "competencia_level": row.get("competencia_level", ""),
                            "disponibilidad": row.get("disponibilidad", ""),
                            "source": "file:mentores.csv",
                        }
                    )
        self._file_cache[cache_key] = rows
        return rows

    def _load_readable_mentor_profiles(self) -> List[Dict[str, Any]]:
        """
        Load human-readable mentor profiles from backend/data/mentors.csv.
        """
        cache_key = "file_mentors_readable"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        rows: List[Dict[str, Any]] = []
        path = self.data_root / "mentors.csv"
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    rows.append(
                        {
                            "mentor_id": row.get("mentor_name", ""),
                            "mentor_name": row.get("mentor_name", ""),
                            "role": row.get("role", ""),
                            "expertise": row.get("expertise", ""),
                            "availability": row.get("availability", ""),
                            "email": row.get("email", ""),
                            "source": "file:mentors.csv",
                        }
                    )
        self._file_cache[cache_key] = rows
        return rows

    def _build_course_candidates(
        self,
        supabase_rows: List[Dict[str, Any]],
        file_rows: List[Dict[str, Any]],
    ) -> List[Candidate]:
        merged: Dict[str, Candidate] = {}

        for row in supabase_rows:
            title = row.get("title") or ""
            key = _normalize_title(title)
            if not key:
                continue
            text = " ".join(
                [
                    str(row.get("title", "")),
                    str(row.get("department", "")),
                    str(row.get("skill_level", "")),
                ]
            )
            merged[key] = Candidate(
                item_type="course",
                title=str(title),
                description=text.strip(),
                source="supabase:courses",
                metadata=row,
            )

        for row in file_rows:
            title = row.get("title") or ""
            key = _normalize_title(title)
            if not key:
                continue
            text = " ".join(
                [
                    str(row.get("title", "")),
                    str(row.get("description", "")),
                    str(row.get("technologies", "")),
                    str(row.get("department", "")),
                    str(row.get("skill_level", "")),
                ]
            )
            candidate = Candidate(
                item_type="course",
                title=str(title),
                description=text.strip(),
                source=str(row.get("source", "file")),
                metadata=row,
            )
            if key in merged:
                merged[key].description = (merged[key].description + " " + candidate.description).strip()
                combined = {**merged[key].metadata}
                for meta_key, meta_value in candidate.metadata.items():
                    if combined.get(meta_key) in (None, "", []):
                        combined[meta_key] = meta_value
                merged[key].metadata = combined
            else:
                merged[key] = candidate

        return list(merged.values())

    def _build_mentor_candidates(
        self,
        supabase_rows: List[Dict[str, Any]],
        file_rows: List[Dict[str, Any]],
    ) -> List[Candidate]:
        merged: Dict[str, Candidate] = {}

        for row in supabase_rows:
            title = row.get("nombre") or row.get("mentor_name") or ""
            if _is_code_like_name(str(title)):
                # Skip opaque IDs so final recommendations use readable names.
                continue
            key = _normalize_title(str(title))
            if not key:
                continue
            specialties = row.get("especialidades", [])
            if isinstance(specialties, list):
                specialties_text = " ".join(str(item) for item in specialties)
            else:
                specialties_text = str(specialties)
            text = " ".join([str(title), specialties_text])
            merged[key] = Candidate(
                item_type="mentor",
                title=str(title),
                description=text.strip(),
                source="supabase:mentores",
                metadata=row,
            )

        for row in file_rows:
            title = row.get("mentor_name") or row.get("nombre", "")
            if _is_code_like_name(str(title)):
                continue
            key = _normalize_title(str(title))
            if not key:
                continue
            text = " ".join(
                [
                    str(title),
                    str(row.get("role", "")),
                    str(row.get("especialidades", "") or row.get("expertise", "")),
                ]
            )
            candidate = Candidate(
                item_type="mentor",
                title=str(title),
                description=text.strip(),
                source=str(row.get("source", "file")),
                metadata=row,
            )
            if key in merged:
                merged[key].description = (merged[key].description + " " + candidate.description).strip()
                merged[key].metadata = {**candidate.metadata, **merged[key].metadata}
            else:
                merged[key] = candidate

        return list(merged.values())

    def _rank_courses(
        self,
        candidates: List[Candidate],
        query_tokens: Set[str],
        skill_tokens: Set[str],
        employee_ctx: Dict[str, Any],
        previous_titles: Set[str],
        top_k: int,
    ) -> List[Candidate]:
        department = str(employee_ctx.get("department", "")).lower()
        ai_usage = _safe_float(employee_ctx.get("ai_usage_frequency", 3), 3.0)
        self_efficacy = _safe_float(employee_ctx.get("self_efficacy", 5.0), 5.0)
        expected_level = 2 if ai_usage >= 4 and self_efficacy >= 5.5 else 1

        ranked: List[Candidate] = []
        for candidate in candidates:
            text_tokens = _tokenize(candidate.description)
            goal_similarity = _jaccard(query_tokens, text_tokens)
            skill_similarity = _jaccard(skill_tokens, text_tokens) if skill_tokens else goal_similarity

            dept_text = " ".join(
                [
                    str(candidate.metadata.get("department", "")),
                    str(candidate.metadata.get("categoria", "")),
                ]
            ).lower()
            department_fit = 1.0 if department and department in dept_text else 0.45

            raw_level = str(
                candidate.metadata.get("skill_level")
                or candidate.metadata.get("nivel")
                or ""
            ).lower()
            level_map = {"principiante": 0, "beginner": 0, "intermedio": 1, "intermediate": 1, "avanzado": 2, "advanced": 2}
            candidate_level = level_map.get(raw_level, 1)
            level_fit = max(0.0, 1.0 - (abs(expected_level - candidate_level) * 0.5))

            completion = _normalize_ratio(candidate.metadata.get("avg_completion_rate"), 0.5)
            improvement = _normalize_ratio(candidate.metadata.get("avg_autoeficacia_improvement"), 0.5)
            perf_signal = (completion + improvement) / 2.0

            novelty = 0.0 if _normalize_title(candidate.title) in previous_titles else 1.0

            score = (
                (0.36 * goal_similarity)
                + (0.20 * skill_similarity)
                + (0.14 * department_fit)
                + (0.12 * level_fit)
                + (0.13 * perf_signal)
                + (0.05 * novelty)
            )
            score = max(0.0, min(1.0, score))

            reasons = []
            if goal_similarity >= 0.12:
                reasons.append("High relevance to current goal")
            if skill_similarity >= 0.10:
                reasons.append("Skill alignment with employee intent")
            if department_fit >= 0.9:
                reasons.append("Department-aligned learning path")
            if level_fit >= 0.75:
                reasons.append("Appropriate difficulty for profile")
            if novelty >= 0.9:
                reasons.append("Diversifies previous recommendations")

            candidate.score = score
            candidate.breakdown = {
                "goal_similarity": round(goal_similarity, 4),
                "skill_similarity": round(skill_similarity, 4),
                "department_fit": round(department_fit, 4),
                "level_fit": round(level_fit, 4),
                "performance_signal": round(perf_signal, 4),
                "novelty": round(novelty, 4),
            }
            candidate.reasons = reasons[:3]
            ranked.append(candidate)

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def _rank_mentors(
        self,
        candidates: List[Candidate],
        query_tokens: Set[str],
        skill_tokens: Set[str],
        employee_ctx: Dict[str, Any],
        top_k: int,
    ) -> List[Candidate]:
        department = str(employee_ctx.get("department", "")).lower()
        ranked: List[Candidate] = []

        for candidate in candidates:
            text_tokens = _tokenize(candidate.description)
            skill_similarity = _jaccard(skill_tokens or query_tokens, text_tokens)
            query_similarity = _jaccard(query_tokens, text_tokens)

            raw_availability = candidate.metadata.get("disponibilidad") or candidate.metadata.get("availability")
            availability_hours = _parse_weekly_hours(raw_availability)
            availability_fit = max(0.0, min(1.0, availability_hours / 8.0))

            raw_competence = candidate.metadata.get("competencia_level")
            competence = max(0.0, min(1.0, _safe_float(raw_competence, 3.0) / 5.0))

            dept_fit = 1.0 if department and department in candidate.description.lower() else 0.5

            score = (
                (0.42 * skill_similarity)
                + (0.20 * query_similarity)
                + (0.18 * availability_fit)
                + (0.15 * competence)
                + (0.05 * dept_fit)
            )
            score = max(0.0, min(1.0, score))

            reasons = []
            if skill_similarity >= 0.12:
                reasons.append("Mentor expertise matches target skills")
            if availability_fit >= 0.5:
                reasons.append("Good current availability")
            if competence >= 0.7:
                reasons.append("Strong mentoring competency level")

            candidate.score = score
            candidate.breakdown = {
                "skill_similarity": round(skill_similarity, 4),
                "query_similarity": round(query_similarity, 4),
                "availability_fit": round(availability_fit, 4),
                "competence": round(competence, 4),
                "department_fit": round(dept_fit, 4),
            }
            candidate.reasons = reasons[:3]
            ranked.append(candidate)

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def _build_evaluation_snapshot(
        self,
        query_tokens: Set[str],
        ranked_courses: List[Candidate],
        ranked_mentors: List[Candidate],
    ) -> Dict[str, Any]:
        top_course_score = ranked_courses[0].score if ranked_courses else 0.0
        top_mentor_score = ranked_mentors[0].score if ranked_mentors else 0.0
        avg_course_score = sum(item.score for item in ranked_courses) / len(ranked_courses) if ranked_courses else 0.0
        avg_mentor_score = sum(item.score for item in ranked_mentors) / len(ranked_mentors) if ranked_mentors else 0.0

        return {
            "query_token_count": len(query_tokens),
            "course_candidates_ranked": len(ranked_courses),
            "mentor_candidates_ranked": len(ranked_mentors),
            "top_course_score": round(top_course_score, 4),
            "top_mentor_score": round(top_mentor_score, 4),
            "avg_course_score": round(avg_course_score, 4),
            "avg_mentor_score": round(avg_mentor_score, 4),
        }

"""
Data Manager: Acceso a datos desde Supabase.
RAG context vía SQL queries.
"""

import logging
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
from supabase import Client

logger = logging.getLogger(__name__)

FIRST_NAME_BY_INITIAL = {
    "A": "Alejandro",
    "B": "Beatriz",
    "C": "Carlos",
    "D": "Daniel",
    "E": "Elena",
    "F": "Fernando",
    "G": "Gabriel",
    "H": "Hector",
    "I": "Irene",
    "J": "Javier",
    "K": "Karla",
    "L": "Lucia",
    "M": "Marta",
    "N": "Nuria",
    "O": "Oscar",
    "P": "Paula",
    "Q": "Quique",
    "R": "Raul",
    "S": "Sofia",
    "T": "Teresa",
    "U": "Unai",
    "V": "Valeria",
    "W": "William",
    "X": "Xavier",
    "Y": "Yolanda",
    "Z": "Zoe",
}

LAST_NAME_BY_INITIAL_1 = {
    "A": "Alonso",
    "B": "Blanco",
    "C": "Castro",
    "D": "Dominguez",
    "E": "Esteban",
    "F": "Fernandez",
    "G": "Garcia",
    "H": "Herrera",
    "I": "Iglesias",
    "J": "Jimenez",
    "K": "Keller",
    "L": "Lopez",
    "M": "Martinez",
    "N": "Navarro",
    "O": "Ortega",
    "P": "Perez",
    "Q": "Quintero",
    "R": "Rodriguez",
    "S": "Sanchez",
    "T": "Torres",
    "U": "Urrutia",
    "V": "Vega",
    "W": "Williams",
    "X": "Ximenez",
    "Y": "Yanez",
    "Z": "Zamora",
}

LAST_NAME_BY_INITIAL_2 = {
    "A": "Alvarez",
    "B": "Benitez",
    "C": "Cabrera",
    "D": "Diaz",
    "E": "Escobar",
    "F": "Flores",
    "G": "Gomez",
    "H": "Hidalgo",
    "I": "Izquierdo",
    "J": "Jurado",
    "K": "Khan",
    "L": "Lara",
    "M": "Molina",
    "N": "Nunez",
    "O": "Olivares",
    "P": "Prieto",
    "Q": "Quevedo",
    "R": "Ruiz",
    "S": "Suarez",
    "T": "Trujillo",
    "U": "Ubeda",
    "V": "Vargas",
    "W": "Wolf",
    "X": "Xuarez",
    "Y": "Yepes",
    "Z": "Zarate",
}

class DataManager:
    """Gestiona acceso a datos desde Supabase."""
    
    def __init__(self, supabase_client: Client):
        """
        Args:
            supabase_client: Cliente de Supabase inicializado
        """
        self.db = supabase_client
        logger.info("DataManager initialized")

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Convert values to JSON-serializable primitives."""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {k: DataManager._normalize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [DataManager._normalize_value(v) for v in value]
        return value

    @staticmethod
    def _ascii_upper_letters(value: Any) -> str:
        """Normalize text and keep only ASCII uppercase letters."""
        text = unicodedata.normalize("NFKD", str(value or ""))
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return "".join(ch for ch in text.upper() if "A" <= ch <= "Z")

    @staticmethod
    def _slug(value: str) -> str:
        """Create a lowercase ASCII slug fragment."""
        text = unicodedata.normalize("NFKD", value or "")
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-zA-Z0-9]+", ".", text).strip(".").lower()
        text = re.sub(r"\.+", ".", text)
        return text or "mentor"

    @staticmethod
    def _is_initials_code(value: str) -> bool:
        """
        Detect 2-5 uppercase initials-like codes (e.g., CDO, MLS, JJO).
        """
        cleaned = (value or "").strip()
        return bool(re.fullmatch(r"[A-Z]{2,5}", cleaned))

    def _mentor_full_name_from_initials(self, initials: str) -> str:
        """
        Deterministically expand initials into a plausible full name.
        """
        letters = self._ascii_upper_letters(initials)
        if len(letters) < 3:
            letters = (letters + "AAA")[:3]
        else:
            letters = letters[:3]

        first = FIRST_NAME_BY_INITIAL.get(letters[0], "Alejandro")
        last_1 = LAST_NAME_BY_INITIAL_1.get(letters[1], "Garcia")
        last_2 = LAST_NAME_BY_INITIAL_2.get(letters[2], "Ruiz")
        return f"{first} {last_1} {last_2}"

    def _mentor_contact_payload(
        self,
        full_name: str,
        initials: str,
    ) -> Dict[str, str]:
        """
        Create synthetic but consistent contact fields for mentor suggestions.
        """
        parts = [part for part in full_name.split(" ") if part]
        first = parts[0] if parts else "mentor"
        last = parts[1] if len(parts) > 1 else "advisor"
        email_local = f"{self._slug(first)}.{self._slug(last)}"
        initials_slug = self._slug(initials)
        if initials_slug:
            email_local = f"{email_local}.{initials_slug}"
        teams_alias = f"{self._slug(first)}.{self._slug(last)}"

        return {
            "email": f"{email_local}@scalian.com",
            "teams": f"@{teams_alias}",
            "contact_channel": "Correo interno o Microsoft Teams",
        }

    def _enrich_mentor_identity(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure mentor rows are human-readable and include contact data.
        """
        enriched = dict(row)
        raw_name = str(enriched.get("nombre") or enriched.get("mentor_name") or "").strip()
        raw_id = str(enriched.get("mentor_id") or "").strip()
        initials_source = raw_name or raw_id
        initials = self._ascii_upper_letters(initials_source)[:5]

        if raw_name and not self._is_initials_code(self._ascii_upper_letters(raw_name)):
            full_name = raw_name
        else:
            full_name = self._mentor_full_name_from_initials(initials_source)

        contact = self._mentor_contact_payload(full_name=full_name, initials=initials)

        # Keep original initials for traceability, expose human-readable name for chatbot.
        enriched["mentor_initials"] = initials or raw_name or raw_id
        enriched["nombre_codigo"] = raw_name or raw_id
        enriched["nombre"] = full_name
        enriched["mentor_name"] = full_name
        enriched["email"] = contact["email"]
        enriched["teams"] = contact["teams"]
        enriched["contact_channel"] = contact["contact_channel"]
        return enriched

    def _safe_select(
        self,
        table: str,
        employee_id: str,
        order_by: Optional[str] = None,
        desc: bool = True,
    ) -> list[dict]:
        """
        Safe helper to fetch all rows for an employee from a table.

        Returns [] when the table/query is unavailable instead of failing hard.
        """
        try:
            query = self.db.table(table).select("*").eq("employee_id", employee_id)
            if order_by:
                query = query.order(order_by, desc=desc)
            response = query.execute()
            rows = response.data if response and response.data else []
            return [self._normalize_value(r) for r in rows]
        except Exception as e:
            logger.warning(
                "Could not load %s rows for employee %s: %s",
                table,
                employee_id,
                e,
            )
            return []

    def get_employee_full_profile(self, employee_id: str) -> Dict[str, Any]:
        """
        Get the full available profile for an employee across Supabase tables.

        Includes:
        - all columns from `employees`
        - all rows from `employee_assessments`
        - all rows from `survey_answers`
        """
        try:
            emp_response = (
                self.db.table("employees")
                .select("*")
                .eq("employee_id", employee_id)
                .single()
                .execute()
            )
            employee_row = self._normalize_value(emp_response.data or {})

            assessments = self._safe_select(
                table="employee_assessments",
                employee_id=employee_id,
                order_by="created_at",
                desc=True,
            )
            survey_answers = self._safe_select(
                table="survey_answers",
                employee_id=employee_id,
                order_by="created_at",
                desc=True,
            )
            recommendation_events = self._safe_select(
                table="recommendation_events",
                employee_id=employee_id,
                order_by="created_at",
                desc=True,
            )

            latest_assessment = assessments[0] if assessments else {}
            latest_survey = survey_answers[0] if survey_answers else {}
            latest_recommendation_event = (
                recommendation_events[0] if recommendation_events else {}
            )

            full_profile = {
                "employee": employee_row,
                "employee_assessments": assessments,
                "survey_answers": survey_answers,
                "recommendation_events": recommendation_events,
                "latest_assessment": latest_assessment,
                "latest_survey_answer": latest_survey,
                "latest_recommendation_event": latest_recommendation_event,
            }

            logger.info(
                (
                    "Full profile loaded for %s "
                    "(assessments=%s, survey_answers=%s, recommendation_events=%s)"
                ),
                employee_id,
                len(assessments),
                len(survey_answers),
                len(recommendation_events),
            )
            return full_profile

        except Exception as e:
            logger.error(f"Error loading full employee profile for {employee_id}: {e}")
            return {}

    def get_employee_context(self, employee_id: str) -> Dict:
        """
        Obtiene contexto de empleado + payload completo para el chatbot.

        Returns:
            A compact context with key features and a `employee_full_profile`
            block that contains all available employee rows in Supabase.
        """
        try:
            full_profile = self.get_employee_full_profile(employee_id)
            if not full_profile:
                return {}

            emp_data = full_profile.get("employee", {})
            latest_assessment = full_profile.get("latest_assessment", {})
            latest_survey = full_profile.get("latest_survey_answer", {})

            context = {
                "employee_id": emp_data.get("employee_id"),
                "department": emp_data.get("department"),
                "education_level": emp_data.get("education_level"),
                "ai_usage_frequency": latest_survey.get("ai_usage_frequency", 3),
                "motivation": float(latest_assessment.get("motivacion", 5.0)),
                "self_efficacy": float(latest_assessment.get("autoeficacia", 5.0)),
                "age": emp_data.get("age"),
                "years_in_company": emp_data.get("years_in_company"),
                # Full payload for factual Q&A.
                "employee_full_profile": full_profile,
            }

            logger.info("Employee context loaded for %s", employee_id)
            return context

        except Exception as e:
            logger.error(f"Error loading employee context: {e}")
            return {}

    @staticmethod
    def _compact_record(record: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
        """Keep only allowed keys with non-empty values."""
        compact: Dict[str, Any] = {}
        for key in allowed_keys:
            if key not in record:
                continue
            value = record.get(key)
            if value in (None, "", [], {}):
                continue
            compact[key] = value
        return compact

    @staticmethod
    def _keys_matching(record: Dict[str, Any], patterns: List[str], limit: int = 20) -> List[str]:
        """Return keys that contain any of the provided patterns."""
        keys = []
        for key in record.keys():
            key_lc = str(key).lower()
            if any(pattern in key_lc for pattern in patterns):
                keys.append(str(key))
        return sorted(keys)[:limit]

    def get_retrieved_facts_for_query(
        self,
        user_message: str,
        employee_ctx: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Structured retrieval: return only query-relevant employee facts.

        This avoids dumping full profile rows into the LLM prompt.
        """
        full_profile = employee_ctx.get("employee_full_profile") or {}
        if not full_profile:
            employee_id = employee_ctx.get("employee_id")
            if employee_id:
                full_profile = self.get_employee_full_profile(str(employee_id))
        if not full_profile:
            return {"source": "structured_db_retrieval", "scope": [], "facts": {}}

        text = (user_message or "").lower()
        scope = {"core_profile"}

        def has_any(keywords: List[str]) -> bool:
            return any(keyword in text for keyword in keywords)

        if has_any(["años", "anos", "antig", "years", "tenure", "empresa", "compañ", "compania"]):
            scope.add("tenure")
        if has_any(["edad", "age", "gender", "género", "genero", "department", "departamento", "education", "educa", "sector", "rol", "role"]):
            scope.add("identity")
        if has_any(["ia", "ai", "chatgpt", "gemini", "copilot", "frecuencia", "usage", "uso", "integr", "herramienta", "tool"]):
            scope.add("ai_usage")
        if has_any(["motiv", "autoefic", "depend", "riesgo", "risk", "assessment", "evalu", "score", "puntu"]):
            scope.add("assessments")
        if has_any(["curso", "course", "mentor", "plan", "recomend", "training", "formaci", "programa", "program"]):
            scope.add("recommendations")

        # For broad/ambiguous questions, provide balanced compact context.
        if scope == {"core_profile"}:
            scope.update({"identity", "ai_usage", "assessments"})

        facts: Dict[str, Any] = {}
        employee = full_profile.get("employee", {}) or {}
        latest_assessment = full_profile.get("latest_assessment", {}) or {}
        latest_survey = full_profile.get("latest_survey_answer", {}) or {}
        latest_recommendation = full_profile.get("latest_recommendation_event", {}) or {}
        assessments = full_profile.get("employee_assessments", []) or []
        survey_answers = full_profile.get("survey_answers", []) or []
        recommendation_events = full_profile.get("recommendation_events", []) or []

        facts["employee"] = self._compact_record(
            employee,
            [
                "employee_id",
                "age",
                "gender",
                "department",
                "years_in_company",
                "education_level",
                "technical_role",
                "sector",
            ],
        )

        if "ai_usage" in scope:
            ai_keys = self._keys_matching(
                latest_survey,
                ["ai", "ia", "chatgpt", "gemini", "copilot", "lms", "frecuencia", "usage", "uso", "integr", "herramienta", "tool", "prefer"],
            )
            if not ai_keys:
                ai_keys = sorted(list(latest_survey.keys()))[:12]
            facts["latest_survey_answer"] = self._compact_record(latest_survey, ai_keys)
            facts["survey_answers_count"] = len(survey_answers)

        if "assessments" in scope:
            assessment_keys = self._keys_matching(
                latest_assessment,
                ["motiv", "autoefic", "depend", "risk", "score", "assessment", "evalu", "confidence", "created"],
            )
            if not assessment_keys:
                assessment_keys = sorted(list(latest_assessment.keys()))[:12]
            facts["latest_assessment"] = self._compact_record(latest_assessment, assessment_keys)
            facts["assessments_count"] = len(assessments)

        if "recommendations" in scope:
            facts["latest_recommendation_event"] = self._compact_record(
                latest_recommendation,
                ["course_recommended", "plan_generated", "created_at", "session_id"],
            )
            facts["recommendation_events_count"] = len(recommendation_events)

        # `tenure` and `identity` are already covered in `employee`.

        return {
            "source": "structured_db_retrieval",
            "scope": sorted(scope),
            "facts": facts,
        }

    def get_department_insights(self, department: str) -> Dict: 
        """
        Obtiene insights del departamento.
        
        Args:
            department: Nombre del departamento
            
        Returns:
            {
                "avg_motivation": 7.2,
                "avg_self_efficacy": 7.8,
                "avg_ai_usage": 3.4,
                "avg_dependency_risk": 3.1,
                "count_employees": 32
            }
        """
        try: 
            # Obtener empleados del departamento
            dept_employees = self.db.table("employees").select(
                "employee_id"
            ).eq("department", department).execute()
            
            dept_ids = [e["employee_id"] for e in dept_employees.data]
            
            # Si no hay empleados en el departamento, devolvemos solo el conteo
            if not dept_ids:
                return {"count_employees": 0}
            
            # Query a employee_assessments solo para empleados del departamento
            response = (
                self.db.table("employee_assessments")
                .select("employee_id, motivacion, autoeficacia, dependencia")
                .eq("assessment_type", "baseline")
                .in_("employee_id", dept_ids)
                .execute()
            )
            
            # Recalcular con pandas si hay datos de assessments
            if response.data:
                df = pd.DataFrame(response.data)
                avg_motivation = float(df["motivacion"].mean()) if "motivacion" in df.columns and not df["motivacion"].empty else 0.0
                avg_self_efficacy = float(df["autoeficacia"].mean()) if "autoeficacia" in df.columns and not df["autoeficacia"].empty else 0.0
                avg_dependency = float(df["dependencia"].mean()) if "dependencia" in df.columns and not df["dependencia"].empty else 0.0
            else:
                # Sin datos de assessments, devolvemos 0.0 como promedio
                avg_motivation = 0.0
                avg_self_efficacy = 0.0
                avg_dependency = 0.0
            
            count = len(dept_ids)
            
            insights = {
                "avg_motivation": avg_motivation,
                "avg_self_efficacy": avg_self_efficacy,
                "avg_ai_usage": 3.4,
                "avg_dependency_risk": avg_dependency,
                "learning_preference": "practical",
                "common_barriers": ["time", "confidence", "relevance"],
                "count_employees": count
            }
            
            logger.info(f"Department insights loaded for {department}")
            return insights
        
        except Exception as e:
            logger.error(f"Error loading department insights: {e}")
            return {"count_employees": 0}
    
    def get_similar_profiles(
        self, 
        department: str,
        ai_usage_frequency: int,
        education_level: str,
        limit: int = 10
    ) -> Dict:
        """
        Obtiene empleados similares (mismo dpto, ai_usage, educación). 
        
        Args: 
            department, ai_usage_frequency (1-5), education_level, limit
        
        Returns:
            {
                "count": 12,
                "summary": "12 empleados similares",
                "avg_improvement": 24,
                "top_courses": ["ML Masterclass", "Python Advanced"],
                "success_rate": 0.78
            }
        """
        try:
            # Buscar empleados similares
            similar_response = self.db.table("employees").select(
                "employee_id"
            ).eq("department", department).eq(
                "education_level", education_level
            ).limit(limit).execute()
            
            similar_count = len(similar_response.data) if similar_response.data else 0
            
            result = {
                "count": similar_count,
                "summary": f"{similar_count} empleados similares en {department}",
                "avg_improvement": 24, #Placeholder
                "top_courses": ["ML Masterclass", "Python Advanced"],
                "success_rate": 0.78
            }
            
            logger.info(f"Similar profiles found: {similar_count}")
            return result
        
        except Exception as e:
            logger.error(f"Error loading similar profiles: {e}")
            return {"count": 0}
    
    def get_top_courses(
        self,
        department: str,
        limit: int = 5,
    ) -> List[Dict]:
        """
        Obtiene top coursos para un departamento.
        
        Args:
            department, limit
            
        Returns:
            [
                {
                    "title": "ML Masterclass",
                    "avg_autoeficacia_improvement": 1.5,
                    "avg_completion_rate": 0.85,
                },
                ...
            ]
        """
        try:
            response = self.db.table("courses").select(
                "title, avg_autoeficacia_improvement, avg_completion_rate"
            ).eq("department", department).order(
                "avg_completion_rate", desc=True
            ).limit(limit).execute()
            
            courses = response.data if response.data else []
            logger.info(f"Top {len(courses)} courses loaded for {department}")
            return courses
        
        except Exception as e:
            logger.error(f"Error loading top courses: {e}")
            return []

    def get_course_catalog(
        self,
        limit: int = 200,
        department: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve course catalog rows from Supabase with optional department filter.
        """
        try:
            query = self.db.table("courses").select("*")
            if department and str(department).strip():
                query = query.eq("department", str(department).strip())
            response = query.limit(limit).execute()
            rows = response.data if response and response.data else []
            return [self._normalize_value(row) for row in rows]
        except Exception as e:
            logger.error(f"Error loading course catalog: {e}")
            return []

    def get_mentor_catalog(self, limit: int = 200) -> List[Dict]:
        """
        Retrieve mentor catalog rows from Supabase.
        """
        try:
            response = self.db.table("mentores").select("*").limit(limit).execute()
            rows = response.data if response and response.data else []
            normalized_rows = [self._normalize_value(row) for row in rows]
            return [self._enrich_mentor_identity(row) for row in normalized_rows]
        except Exception as e:
            logger.error(f"Error loading mentor catalog: {e}")
            return []
        
    def get_course_by_skills(self, skills: List[str]) -> List[Dict]:
        """
        Obtiene cursos que matchean con skills.
        
        Args: 
            skills: Lista de skills ["ML", "Python"]
        
        Returns:
            List[Dict] de cursos
        """
        try:
            # Placeholder: simplemente retorna cursos
            response = self.db.table("courses").select("*").limit(10).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error loading courses by skills: {e}")
            return []
    
    def get_mentor_recommendations(self, especialidades: list[str], limit: int = 2) -> list[dict]:
        """
        Obtiene recomendaciones de mentores basados en especialidades de cursos.
        Filtra, ordena y limita directamente en Supabase para mayor rendimiento.
        """
        try:
            if not especialidades:
                logger.info("No specialties provided for mentor recommendations")
                return []
                
            # Delegamos carga a Supabase: Overlap (&& en SQL), Sort y Limit
            response = (
                self.db.table("mentores")
                .select("mentor_id, nombre, especialidades, competencia_level, disponibilidad")
                .gt("disponibilidad", 0)
                .overlaps("especialidades", especialidades)
                .order("competencia_level", desc=True)
                .limit(limit)
                .execute()
            )
            
            mentores_data = response.data if response.data else []
            
            if not mentores_data:
                logger.info(f"No mentores found in database for specialties: {especialidades}")
                return []

            mentores_data = [
                self._enrich_mentor_identity(self._normalize_value(row))
                for row in mentores_data
            ]
            logger.info(f"Found {len(mentores_data)} mentores matching specialties: {especialidades}")
            return mentores_data
            
        except Exception as e:
            logger.error(f"Error loading mentor recommendations: {e}")
            return []
        
    def get_relevant_programs(
        self,
        tecnologias: List[str],
        nivel: Optional[str] = None, 
        limit: int = 3
    ) -> List[Dict]:
        """
        Obtiene programas de formación relevantes.
        
        Args:
            tecnologias: Lista de tecnologías (ej: ["Python", "AWS"])
            nivel: Nivel optional (ej: "Intermedio", "Avanzado")
            limit: Número máximo de programas
            
        Returns:
            [
                {
                    "title": "Python Advanced",
                    "department": "Tech",
                    "skill_level": "Avanzado",
                    "avg_autoeficacia_improvement": 1.5,
                    "avg_completion_rate": 0.85
                },
                ...
            ]
        """
        try:
            # Fetch ALL cursos
            query = self.db.table("courses").select(
                "title, department, skill_level, avg_autoeficacia_improvement, avg_completion_rate"
            )
            
            # Filtrar por nivel si se proporciona
            if nivel:
                query = query.eq("skill_level", nivel)
                
            response = query.order(
                "avg_completion_rate", desc=True
            ).limit(limit * 2).execute()    # Fetch más para filtrar despues
            
            courses = response.data if response.data else []
            
            if not courses:
                logger.info(f"No programs found for technologies: {tecnologias}")
                return []
            
            # Post-filter por tecnologías (simple: check title contains tech keywords)
            matching_programs = []
            for course in courses:
                course_title = course.get("title", "").lower()
                # Verificar si title contiene alguna tecnología
                if any(tech.lower() in course_title for tech in tecnologias):
                    matching_programs.append(course)
                # Si no hay matches por título, igual incluir (no ser muy restrictivo)
                elif len(matching_programs) < limit:
                    matching_programs.append(course)
                    
            result = matching_programs[:limit]
            logger.info(f"Found {len(result)} relevant programs for technologies: {tecnologias}")
            return result
        
        except Exception as e:
            logger.error(f"Error loading relevant programs: {e}")
            return []
            
            
            
        
            

"""
Data Manager: Acceso a datos desde Supabase.
RAG context vía SQL queries.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd
from supabase import Client

logger = logging.getLogger(__name__)

class DataManager:
    """Gestiona acceso a datos desde Supabase."""
    
    def __init__(self, supabase_client: Client):
        """
        Args:
            supabase_client: Cliente de Supabase inicializado
        """
        self.db = supabase_client
        logger.info("DataManager initialized")
        
    def get_employee_context(self, employee_id: str) -> Dict:
        """
        Obtiene contexto del empleado desde tabla employees.
        
        Args:
            employee_id: ID empleado (ej: "1XVWCBPH")
        
        Returns: 
            {
                "employee_id": "1XVWCBPH",
                "department": "IT",
                "education_level": "Máster",
                "ai_usage_frequency": 2,
                "motivation": 7.5,
                "self_efficacy": 8.0,
                "age": 32,
                "years_in_company": 17
            }
        """
        try:
            # Fetch employee demográfico
            emp_response = self.db.table("employees").select(
                "employee_id, age, gender, department, years_in_company, education_level"
            ).eq("employee_id", employee_id).single().execute()
            
            emp_data = emp_response.data
            
            # Fetch última evaluación baseline
            eval_response = self.db.table("employee_assessments").select(
                "motivacion, autoeficacia"
            ).eq("employee_id", employee_id).eq(
                "assessment_type", "baseline"
            ).order("created_at", desc=True).limit(1).execute()
            
            eval_data = eval_response.data[0] if eval_response.data else {
                "motivacion": 5.0,
                "autoeficacia": 5.0
            }
            
            # Fetch AI usage del survey
            survey_response = self.db.table("survey_answers").select(
                "ai_usage_frequency"
            ).eq("employee_id", employee_id).limit(1).execute()
            
            ai_usage = survey_response.data[0]["ai_usage_frequency"] if survey_response.data else 3
            
            context = {
                "employee_id": emp_data.get("employee_id"),
                "department": emp_data.get("department"),
                "education_level": emp_data.get("education_level"),
                "ai_usage_frequency": ai_usage,
                "motivation": float(eval_data.get("motivacion", 5.0)),
                "self_efficacy": float(eval_data.get("autoeficacia", 5.0)),
                "age": emp_data.get("age"),
                "years_in_company": emp_data.get("years_in_company")                
            }
            
            logger.info(f"Employee context loaded for {employee_id}")
            return context
        
        except Exception as e:
            logger.error(f"Error loading employee context: {e}")
            return {}
    
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
            
            
            
        
            
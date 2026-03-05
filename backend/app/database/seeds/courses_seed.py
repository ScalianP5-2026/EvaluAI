"""
Courses Seed: Insertar cursos de ejemplo en Supabase
"""

import asyncio
import logging
from supabase import Client

logger = logging.getLogger(__name__)

async def seed_courses(supabase: Client) -> bool:
    """
    Inserta 12 cursos de ejemplo en la tabla courses.
    
    Args:
        supabase: Cliente inicializado de Supabase
    
    Returns:
        True si se insertaron todos; False si hay error
    """
    
    courses = [
        {
            "name": "ML Fundamentals Bootcamp",
            "department": "IT",
            "duration_hours": 40,
            "avg_autoeficacia_improvement": 1.8,
            "avg_completion_rate": 0.92,
            "description": "Introducción a Machine Learning desde cero"
        },
        {
            "name": "Python Advanced",
            "department": "IT",
            "duration_hours": 30,
            "avg_autoeficacia_improvement": 1.5,
            "avg_completion_rate": 0.88,
            "description": "Programación avanzada en Python: decoradores, async/await, testing"
        },
        {
            "name": "Data Visualization with Tableau",
            "department": "Analytics",
            "duration_hours": 25,
            "avg_autoeficacia_improvement": 1.2,
            "avg_completion_rate": 0.85,
            "description": "Crear dashboards interactivos y reportes visuales"
        },
        {
            "name": "Leadership Skills",
            "department": "HR",
            "duration_hours": 20,
            "avg_autoeficacia_improvement": 1.4,
            "avg_completion_rate": 0.78,
            "description": "Desarrollo de habilidades de liderazgo y gestión de equipos"
        },
        {
            "name": "SQL Mastery",
            "department": "IT",
            "duration_hours": 35,
            "avg_autoeficacia_improvement": 1.6,
            "avg_completion_rate": 0.90,
            "description": "SQL avanzado: queries complejas, optimización, índices"
        },
        {
            "name": "Communication in English",
            "department": "HR",
            "duration_hours": 45,
            "avg_autoeficacia_improvement": 1.3,
            "avg_completion_rate": 0.75,
            "description": "Comunicación empresarial en inglés: presentaciones y reuniones"
        },
        {
            "name": "Cloud Architecture (AWS)",
            "department": "IT",
            "duration_hours": 50,
            "avg_autoeficacia_improvement": 2.1,
            "avg_completion_rate": 0.95,
            "description": "Diseño e implementación de arquitecturas en AWS"
        },
        {
            "name": "Financial Analysis Basics",
            "department": "Finance",
            "duration_hours": 30,
            "avg_autoeficacia_improvement": 1.1,
            "avg_completion_rate": 0.82,
            "description": "Análisis financiero: ratios, presupuestos deflacionados"
        },
        {
            "name": "Project Management with Agile",
            "department": "Management",
            "duration_hours": 25,
            "avg_autoeficacia_improvement": 1.5,
            "avg_completion_rate": 0.87,
            "description": "Metodologías Agile y Scrum para gestión de proyectos"
        },
        {
            "name": "UX/UI Design Principles",
            "department": "Design",
            "duration_hours": 35,
            "avg_autoeficacia_improvement": 1.7,
            "avg_completion_rate": 0.89,
            "description": "Diseño centrado en usuario: wireframes, prototipos, testing"
        },
        {
            "name": "Customer Success Strategy",
            "department": "Sales",
            "duration_hours": 20,
            "avg_autoeficacia_improvement": 1.2,
            "avg_completion_rate": 0.81,
            "description": "Estrategias de retención y satisfacción del cliente"
        },
        {
            "name": "DevOps & CI/CD Pipeline",
            "department": "IT",
            "duration_hours": 40,
            "avg_autoeficacia_improvement": 1.9,
            "avg_completion_rate": 0.91,
            "description": "Automatización de deployments y monitoreo en producción"
        }
    ]
    
    try: 
        logger.info(f"Seeding {len(courses)} courses into Supabase...")
        
        # Insertar todos de una vez
        response = supabase.table("courses").insert(courses).execute()
        
        if response.data:
            logger.info(f"✓ Inserted {len(response.data)} courses successfully")
            return True
        else:
            logger.warning(f"Insert returned no data: {response}")
            return False
        
    except Exception as e:
        logger.error(f"Error seeding courses: {e}")
        return False


async def main():
    """
    Script standalone para ejecutar seed manualmente.
    
    Uso: python -m app.database.seeds.courses_seed
    """
    from app.config import get_supabase_client
    
    logger.basicConfig(level=logging.INFO)
    supabase = get_supabase_client()
    
    success = await seed_courses(supabase)
    if success:
        print("✅ Seed completado")
    else:
        print("❌ Seed falló")


if __name__ == "__main__":
    asyncio.run(main())
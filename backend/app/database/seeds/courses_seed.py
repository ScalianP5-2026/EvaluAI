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
            "title": "ML Fundamentals Bootcamp",
            "department": "IT",
            "skill_level": "Beginner",
            "avg_autoeficacia_improvement": 1.8,
            "avg_completion_rate": 0.92,
        },
        {
            "title": "Python Advanced",
            "department": "IT",
            "skill_level": "Advanced",
            "avg_autoeficacia_improvement": 1.5,
            "avg_completion_rate": 0.88,
        },
        {
            "title": "Data Visualization with Tableau",
            "department": "Analytics",
            "skill_level": "Intermediate",
            "avg_autoeficacia_improvement": 1.2,
            "avg_completion_rate": 0.85,
        },
        {
            "title": "Leadership Skills",
            "department": "HR",
            "skill_level": "Intermediate",
            "avg_autoeficacia_improvement": 1.4,
            "avg_completion_rate": 0.78,
        },
        {
            "title": "SQL Mastery",
            "department": "IT",
            "skill_level": "Advanced",
            "avg_autoeficacia_improvement": 1.6,
            "avg_completion_rate": 0.90,
        },
        {
            "title": "Communication in English",
            "department": "HR",
            "skill_level": "Beginner",
            "avg_autoeficacia_improvement": 1.3,
            "avg_completion_rate": 0.75,
        },
        {
            "title": "Cloud Architecture (AWS)",
            "department": "IT",
            "skill_level": "Advanced",
            "avg_autoeficacia_improvement": 2.1,
            "avg_completion_rate": 0.95,
        },
        {
            "title": "Financial Analysis Basics",
            "department": "Finance",
            "skill_level": "Beginner",
            "avg_autoeficacia_improvement": 1.1,
            "avg_completion_rate": 0.82,
        },
        {
            "title": "Project Management with Agile",
            "department": "Management",
            "skill_level": "Intermediate",
            "avg_autoeficacia_improvement": 1.5,
            "avg_completion_rate": 0.87,
        },
        {
            "title": "UX/UI Design Principles",
            "department": "Design",
            "skill_level": "Intermediate",
            "avg_autoeficacia_improvement": 1.7,
            "avg_completion_rate": 0.89,
        },
        {
            "title": "Customer Success Strategy",
            "department": "Sales",
            "skill_level": "Beginner",
            "avg_autoeficacia_improvement": 1.2,
            "avg_completion_rate": 0.81,
        },
        {
            "title": "DevOps & CI/CD Pipeline",
            "department": "IT",
            "skill_level": "Advanced",
            "avg_autoeficacia_improvement": 1.9,
            "avg_completion_rate": 0.91,
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
    
    logging.basicConfig(level=logging.INFO)
    supabase = get_supabase_client()
    
    success = await seed_courses(supabase)
    if success:
        print("✅ Seed completado")
    else:
        print("❌ Seed falló")


if __name__ == "__main__":
    asyncio.run(main())
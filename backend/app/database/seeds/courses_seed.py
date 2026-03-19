"""
Seed: Programas de formación.
Lee programas_formacion.csv e inserta en tabla "courses".
"""

import csv
import logging
from pathlib import Path

from supabase import Client

logger = logging.getLogger(__name__)

async def seed_courses(supabase: Client) -> bool:
    """
    Lee programas_formacion.csv → inserta como cursos en Supabase.    
    Este archivo tiene UNA responsabilidad: Cargar cursos.
    """
    
    csv_path = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "programas_formacion.csv"
    
    if not csv_path.exists():
        logger.warning(f"Courses CSV not found: {csv_path}")
        return False
    
    try: 
        courses = []
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                courses.append({
                    "title": row.get('nombre', '').strip(),
                    "department": row.get('categoria', '').strip(),
                    "skill_level": row.get('nivel', 'Intermedio').strip(),
                    "avg_autoeficacia_improvement": 0.0, # TODO: Desde data real
                    "avg_completion_rate": 0.0,          # TODO: Desde data real
                })
        
        if not courses:
            logger.warning("No courses found in CSV")
            return False
            
        logger.info(f"Seeding {len(courses)} courses...")
        
        response = supabase.table("courses").upsert(
            courses,
            on_conflict="title"
        ).execute()
        
        logger.info(f"✓ Inserted {len(courses)} courses successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error seeding courses: {e}")
        return False
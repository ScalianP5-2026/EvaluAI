"""
Seed: Mentores / Tutores.
Lee mentores.csv e inserta en tabla "mentores".
"""

import csv
import logging
from pathlib import Path

from supabase import Client

logger = logging.getLogger(__name__)

async def seed_mentores(supabase: Client) -> bool:
    """
    Lee mentores.csv -> Inserta en tabla "mentores" de Supabase.
    
    Cargar mentores.
    """
    
    csv_path = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "mentores.csv"
    
    if not csv_path.exists():
        logger.warning(f"Mentores CSV not found: {csv_path}")
        return False
    
    try:
        mentores = []
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                especialidades = [
                    e.strip() for e in row.get('especialidades', '').split('|')
                    if e.strip()
                ]
                
                mentores.append({
                    "mentor_id": row.get('id_mentor', '').strip(),
                    "nombre": row.get('nombre', '').strip(),
                    "especialidades": especialidades,
                    "competencia_level": int(row.get('competencia_level', 1)),
                    "disponibilidad": int(row.get('disponibilidad', 1))
                })
            
        if not mentores:
            logger.warning("No mentores found in CSV")
            return False
        
        logger.info(f"Seeding {len(mentores)} mentores...")
        
        response = supabase.table("mentores").upsert(
            mentores,
            on_conflict="mentor_id"
        ).execute()
            
        logger.info(f"✓ Inserted {len(mentores)} mentores successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error seeding mentores: {e}")
        return False
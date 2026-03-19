"""
User Credentials Seed: Creates mocked email accounts for employees in Supabase.

Reads employee IDs from the survey dataset and generates a unique
firstname.lastname@scalian.com email for each, with password_hash = NULL.
On first login, each employee will set their own password.
"""

import asyncio
import logging
from pathlib import Path

from supabase import Client

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Name Pool for Email Generation
# ═══════════════════════════════════════════════════════════════

FIRST_NAMES = [
    "maria", "carlos", "ana", "pablo", "lucia", "miguel", "elena", "daniel",
    "sofia", "javier", "laura", "fernando", "carmen", "roberto", "isabel",
    "alejandro", "patricia", "antonio", "claudia", "david", "marta", "jorge",
    "raquel", "francisco", "natalia", "manuel", "beatriz", "pedro", "andrea",
    "luis", "cristina", "sergio", "rosa", "rafael", "irene", "alberto",
    "pilar", "enrique", "julia", "oscar", "silvia", "ramon", "alicia",
    "hugo", "paula", "marcos", "teresa", "gabriel", "noelia", "victor",
    "eva", "angel", "rocio", "ivan", "sandra", "adrian", "lorena",
    "tomas", "esther", "nicolas", "marina", "felix", "amparo", "hector",
    "gloria", "santiago", "olga", "cesar", "lourdes", "ruben", "monica",
    "martin", "nuria", "rodrigo", "consuelo", "diego", "susana", "arturo",
    "yolanda", "ignacio", "dolores", "gonzalo", "aurora", "emilio", "encarna",
    "jaime", "celeste", "bruno", "valentina", "mateo", "camila", "leon",
    "jimena", "alonso", "renata", "belen", "ines", "elisa", "clara",
]

LAST_NAMES = [
    "garcia", "martinez", "lopez", "gonzalez", "rodriguez", "fernandez",
    "sanchez", "perez", "gomez", "martin", "jimenez", "ruiz", "hernandez",
    "diaz", "moreno", "alvarez", "muñoz", "romero", "alonso", "gutierrez",
    "navarro", "torres", "dominguez", "vazquez", "ramos", "gil", "ramirez",
    "serrano", "blanco", "molina", "morales", "suarez", "ortega", "delgado",
    "castro", "ortiz", "rubio", "marin", "sanz", "nuñez", "iglesias",
    "medina", "garrido", "cortes", "castillo", "santos", "lozano", "guerrero",
    "cano", "prieto", "mendez", "cruz", "calvo", "gallego", "vidal",
    "leon", "herrera", "marquez", "cabrera", "campos", "vega", "fuentes",
    "carrasco", "diez", "reyes", "caballero", "nieto", "aguilar", "pascual",
    "herrero", "montero", "lorenzo", "hidalgo", "gimenez", "ibañez",
    "ferrer", "duran", "vicente", "benitez", "mora", "santiago", "arias",
    "vargas", "carmona", "crespo", "roman", "pastor", "soto", "saez",
    "velasco", "moya", "soler", "parra", "esteban", "bravo", "rojas",
    "gallardo", "mendoza", "cardenas", "silva",
]


def _generate_emails(employee_ids: list[str]) -> dict[str, str]:
    """
    Generate unique mocked email addresses for a list of employee IDs.
    
    Returns a dict mapping employee_id -> email
    """
    emails: dict[str, str] = {}
    used_emails: set[str] = set()
    
    first_idx = 0
    last_idx = 0
    
    for emp_id in employee_ids:
        # Generate unique email by cycling through name combinations
        attempts = 0
        while attempts < len(FIRST_NAMES) * len(LAST_NAMES):
            first = FIRST_NAMES[first_idx % len(FIRST_NAMES)]
            last = LAST_NAMES[last_idx % len(LAST_NAMES)]
            email = f"{first}.{last}@scalian.com"
            
            if email not in used_emails:
                used_emails.add(email)
                emails[emp_id] = email
                
                # Advance indices for next employee
                first_idx += 1
                if first_idx % len(FIRST_NAMES) == 0:
                    last_idx += 1
                break
            
            first_idx += 1
            if first_idx % len(FIRST_NAMES) == 0:
                last_idx += 1
            attempts += 1
        else:
            # Fallback: use employee_id-based email
            email = f"employee.{emp_id.lower()}@scalian.com"
            emails[emp_id] = email
    
    return emails


async def seed_user_credentials(supabase: Client) -> bool:
    """
    Seed user_credentials table with mocked emails from survey dataset.
    
    Each employee gets a unique firstname.lastname@scalian.com email
    with password_hash = NULL (they'll set their password on first login).
    
    Args:
        supabase: Initialized Supabase client
        
    Returns:
        True if seeding succeeded, False on critical error
    """
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "survey_raw.xlsx"
    
    if not data_path.exists():
        logger.error(f"Dataset file not found: {data_path}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_excel(data_path, engine="openpyxl")
        
        if df.empty:
            logger.error("Dataset file is empty")
            return False
        
        # Extract unique employee IDs
        employee_ids = df["id_empleado"].dropna().astype(str).str.strip().unique().tolist()
        
        if not employee_ids:
            logger.error("No employee IDs found in dataset")
            return False
        
        logger.info(f"Generating emails for {len(employee_ids)} employees...")
        
        # Generate mocked emails
        email_map = _generate_emails(employee_ids)
        
        # Build credential records (password_hash = None for first-time setup)
        credentials = []
        for emp_id, email in email_map.items():
            credentials.append({
                "employee_id": emp_id,
                "email": email,
                "password_hash": None,
                "is_active": True,
            })
        
        # Insert into Supabase
        logger.info(f"Inserting {len(credentials)} user credentials into Supabase...")
        
        try:
            response = supabase.table("user_credentials").insert(credentials).execute()
            if response.data:
                logger.info(f"✓ Inserted {len(response.data)} user credentials")
        except Exception as e:
            if "duplicate" in str(e).lower() or "23505" in str(e):
                logger.info("✓ User credentials already exist (skipping duplicates)")
            else:
                # Try one-by-one for partial insert
                inserted = 0
                for cred in credentials:
                    try:
                        supabase.table("user_credentials").insert([cred]).execute()
                        inserted += 1
                    except Exception as inner_e:
                        if "duplicate" in str(inner_e).lower() or "23505" in str(inner_e):
                            continue
                        else:
                            logger.warning(f"Error inserting {cred['email']}: {inner_e}")
                logger.info(f"✓ Inserted {inserted} new credentials (others already existed)")
        
        # Print credentials table to console
        logger.info("=" * 60)
        logger.info("  EMPLOYEE LOGIN CREDENTIALS (password not set yet)")
        logger.info("=" * 60)
        for emp_id, email in list(email_map.items())[:20]:
            logger.info(f"  {emp_id:<12} → {email}")
        if len(email_map) > 20:
            logger.info(f"  ... and {len(email_map) - 20} more employees")
        logger.info("=" * 60)
        
        return True
        
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {data_path}")
        return False
    except Exception as e:
        if "duplicate" in str(e).lower() or "23505" in str(e):
            logger.info("✓ All user credentials already exist")
            return True
        else:
            logger.error(f"Error seeding user credentials: {e}")
            return False

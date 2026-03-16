"""Load employees and generate fake credentials for the database."""

import logging
from pathlib import Path
import pandas as pd
from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Apuntamos al archivo limpio que ya validaste antes
BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_PATH = BASE_DIR / "data" / "clean" / "survey_clean.csv"

def main() -> None:
    if not CLEAN_PATH.exists():
        logger.error(f"No se encontró el archivo limpio: {CLEAN_PATH}")
        return

    print("Cargando empleados y generando credenciales...")
    df = pd.read_csv(CLEAN_PATH)

    # Filtrar para tener solo una fila por empleado (por si acaso el excel tiene duplicados)
    empleados_unicos = df.drop_duplicates(subset=['id_empleado'])

    supabase = get_supabase_client()
    empleados_batch = []
    credenciales_batch = []

    for _, row in empleados_unicos.iterrows():
        emp_id = str(row['id_empleado']).strip()
        if not emp_id or emp_id.lower() == 'nan':
            continue

        # 1. Preparar el registro para la tabla 'employees'
        empleados_batch.append({
            "employee_id": emp_id,
            "age": int(row['edad']) if pd.notna(row['edad']) else None,
            "gender": str(row['genero']) if pd.notna(row['genero']) else "Sin especificar",
            "department": str(row['departamento']) if pd.notna(row['departamento']) else "Sin asignar"
        })

        # 2. Preparar el registro para 'user_credentials' (Los emails falsos de Nacho)
        email_falso = f"{emp_id.lower()}@empresa.fake"
        credenciales_batch.append({
            "employee_id": emp_id,
            "email": email_falso,
            "password_hash": "password_generica_123", # Contraseña por defecto
            "is_active": True
        })

    if empleados_batch:
        # IMPORTANTE: Subir primero a 'employees' para no romper la Llave Foránea
        supabase.table("employees").upsert(empleados_batch, on_conflict="employee_id").execute()
        logger.info("✅ %s empleados cargados exitosamente.", len(empleados_batch))

        # Luego subir las credenciales de Nacho
        supabase.table("user_credentials").upsert(credenciales_batch, on_conflict="employee_id").execute()
        logger.info("✅ %s credenciales generadas exitosamente.", len(credenciales_batch))
    else:
        logger.warning("No se encontraron empleados válidos para subir.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error al cargar empleados: %s", exc)
        raise
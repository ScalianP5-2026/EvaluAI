"""Load employees securely, updating only if needed and never overwriting existing credentials."""

import logging
from pathlib import Path
import pandas as pd
from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_PATH = BASE_DIR / "data" / "clean" / "survey_clean.csv"

def main() -> None:
    if not CLEAN_PATH.exists():
        logger.error(f"No se encontró el archivo limpio: {CLEAN_PATH}")
        return

    print("Verificando datos de empleados...")
    df = pd.read_csv(CLEAN_PATH)
    empleados_unicos = df.drop_duplicates(subset=['id_empleado'])

    supabase = get_supabase_client()

    # 1. Traer los empleados que YA existen en la base de datos para comparar
    print("Descargando estado actual de la base de datos...")
    db_employees_response = supabase.table("employees").select("employee_id, age, gender, department").execute()
    existing_employees = {emp["employee_id"]: emp for emp in db_employees_response.data}

    # Traer los IDs de los que ya tienen credenciales para no pisar el trabajo de Nacho
    db_credentials_response = supabase.table("user_credentials").select("employee_id").execute()
    existing_credentials = {cred["employee_id"] for cred in db_credentials_response.data}

    empleados_a_subir = []
    credenciales_nuevas = []

    for _, row in empleados_unicos.iterrows():
        emp_id = str(row['id_empleado']).strip()
        if not emp_id or emp_id.lower() == 'nan':
            continue

        # Datos limpios del Excel
        new_age = int(row['edad']) if pd.notna(row['edad']) else None
        new_gender = str(row['genero']) if pd.notna(row['genero']) else "Sin especificar"
        new_dept = str(row['departamento']) if pd.notna(row['departamento']) else "Sin asignar"

        # 2. Verificar si es NUEVO o si hay ACTUALIZACIONES
        if emp_id in existing_employees:
            old_data = existing_employees[emp_id]
            # Solo si hay algún cambio real, lo marcamos para actualizar
            if (old_data.get("age") != new_age or 
                old_data.get("gender") != new_gender or 
                old_data.get("department") != new_dept):
                
                empleados_a_subir.append({
                    "employee_id": emp_id,
                    "age": new_age,
                    "gender": new_gender,
                    "department": new_dept
                })
        else:
            # Es un empleado completamente NUEVO
            empleados_a_subir.append({
                "employee_id": emp_id,
                "age": new_age,
                "gender": new_gender,
                "department": new_dept
            })

        # 3. Credenciales: SOLO creamos si el empleado NO tiene credenciales aún
        if emp_id not in existing_credentials:
            credenciales_nuevas.append({
                "employee_id": emp_id,
                "email": f"{emp_id.lower()}@scalian.com",
                "password_hash": "password_generica_123",
                "is_active": True
            })

    # 4. Ejecutar los cambios en la base de datos
    if empleados_a_subir:
        print(f"Subiendo {len(empleados_a_subir)} actualizaciones/inserciones de empleados...")
        supabase.table("employees").upsert(empleados_a_subir, on_conflict="employee_id").execute()
        logger.info("✅ %s empleados procesados exitosamente.", len(empleados_a_subir))
    else:
        logger.info("✅ No hay cambios nuevos en los empleados. Todo está al día.")

    if credenciales_nuevas:
        print(f"Generando {len(credenciales_nuevas)} credenciales nuevas...")
        supabase.table("user_credentials").insert(credenciales_nuevas).execute()
        logger.info("✅ %s credenciales nuevas generadas.", len(credenciales_nuevas))
    else:
        logger.info("✅ No hizo falta generar credenciales nuevas. El trabajo de Nacho está intacto.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error al procesar empleados: %s", exc)
        raise
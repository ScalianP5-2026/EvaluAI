"""Load survey answers securely fitting the CURRENT database schema (without date column)."""

import logging
from pathlib import Path
import pandas as pd
from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Rutas
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "raw" / "survey_raw.xlsx"
ERRORS_DIR = BASE_DIR / "data" / "errors"
BATCH_SIZE = 100

def _to_int_or_none(value):
    if pd.isna(value): return None
    try: return int(float(value))
    except: return None

def _to_bool_or_none(value):
    if pd.isna(value): return None
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)): return bool(int(value))
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "si", "sí"}: return True
    if text in {"0", "false", "f", "no", "n"}: return False
    return None

def main() -> None:
    if not DATA_PATH.exists():
        logger.error(f"Archivo no encontrado: {DATA_PATH}")
        return

    # Crear carpeta de errores
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    print("Cargando y validando respuestas de encuestas...")
    
    if DATA_PATH.suffix == '.xlsx':
        df = pd.read_excel(DATA_PATH, engine="openpyxl")
    else:
        df = pd.read_csv(DATA_PATH)
        
    df.columns = df.columns.str.lower().str.strip()
    df = df.dropna(subset=['id_empleado'])

    supabase = get_supabase_client()

    # 1. Obtener empleados VÁLIDOS de Supabase
    db_employees = supabase.table("employees").select("employee_id").execute()
    valid_employees = {emp["employee_id"] for emp in db_employees.data}

    records_to_insert = []
    error_records = []

    freq_col = "ai_usage_frequency" if "ai_usage_frequency" in df.columns else "frecuencia_uso_ia"
    chatgpt_col = "uses_chatgpt" if "uses_chatgpt" in df.columns else "usa_chatgpt"

    for _, row in df.iterrows():
        emp_id = str(row['id_empleado']).strip()

        # REGLA 1: Verificar si el usuario existe
        if emp_id not in valid_employees:
            error_records.append({
                "id_empleado": emp_id,
                "motivo": "El usuario no existe en la tabla employees de Supabase",
                "fecha_encuesta": row.get('survey_completed_at', 'Sin fecha')
            })
            continue

        # REGLA 2: Mapear SOLO las columnas que sabemos que la DB actual soporta
        records_to_insert.append({
            "employee_id": emp_id,
            "ai_usage_frequency": _to_int_or_none(row.get(freq_col)),
            "uses_chatgpt": _to_bool_or_none(row.get(chatgpt_col))
        })

    # --- GUARDAR ERRORES EN CSV ---
    if error_records:
        error_file = ERRORS_DIR / "encuestas_rechazadas.csv"
        df_errors = pd.DataFrame(error_records)
        df_errors.to_csv(error_file, index=False, encoding="utf-8-sig")
        print(f"\n⚠️ ATENCIÓN: Se han rechazado {len(error_records)} encuestas.")
        print(f"📁 Tienes un archivo detallado con los errores en: {error_file}")
        print("-" * 60)

    # --- SUBIR REGISTROS VÁLIDOS ---
    if records_to_insert:
        print(f"\nSubiendo {len(records_to_insert)} encuestas válidas al esquema actual...")
        
        # Quitamos duplicados locales para que la base de datos vieja no pete
        deduped = {r["employee_id"]: r for r in records_to_insert}
        final_records = list(deduped.values())

        for i in range(0, len(final_records), BATCH_SIZE):
            batch = final_records[i:i + BATCH_SIZE]
            try:
                # Usamos insert normal porque la tabla no tiene restricción ON CONFLICT
                supabase.table("survey_answers").insert(batch).execute()
            except Exception as e:
                logger.error(f"Error subiendo el bloque {i}: {e}")
        logger.info("✅ %s encuestas subidas con éxito.", len(final_records))
    else:
        logger.info("✅ No hay encuestas nuevas y válidas para subir.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error al procesar las encuestas: %s", exc)
        raise
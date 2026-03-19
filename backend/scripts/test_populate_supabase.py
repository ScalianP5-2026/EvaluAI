import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

OPEN_TEXT_MAX_LENGTH = 500

# Cargar variables de entorno desde el .env en la raiz del proyecto.
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no esta definida. Configurala en tu archivo .env."
    )

engine = create_engine(DATABASE_URL)

# Resolve dataset path relative to project root (works locally and in Docker)
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "survey_raw.xlsx"
if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
df = pd.read_excel(DATA_PATH, engine="openpyxl")

# Asegurar que columnas coincidan con nombres SQL
df.columns = df.columns.str.lower()

# Normalizar columnas de texto abiertas al contrato oficial de DB
open_text_aliases = {
    "comentarios_experiencia_ia": "open_experience_ai_learning",
    "sugerencias_mejora": "open_training_needs",
    "open_experience": "open_experience_ai_learning",
    "experience_ai": "open_experience_ai_learning",
    "ai_learning_comment": "open_experience_ai_learning",
    "open_challenge": "open_challenges_ai_usage",
    "ai_challenges_comment": "open_challenges_ai_usage",
    "training_comment": "open_training_needs",
}
df = df.rename(
    columns={k: v for k, v in open_text_aliases.items() if k in df.columns}
)
for col in [
    "open_experience_ai_learning",
    "open_challenges_ai_usage",
    "open_training_needs",
]:
    if col not in df.columns:
        df[col] = ""
    df[col] = (
        df[col]
        .fillna("")
        .astype(str)
        .str.slice(0, OPEN_TEXT_MAX_LENGTH)
    )

# Convertir rol_tecnico de 0/1 a booleano True/False

# Convertir columnas booleanas de 0/1 a True/False
bool_cols = [
    'rol_tecnico',
    'usa_chatgpt',
    'usa_gemini',
    'usa_copilot',
    'usa_lms_ia',
    'usa_otra_ia'
]
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: True if x == 1 else False)

# Leer los id_empleado existentes en la base de datos
with engine.connect() as conn:
    result = conn.execute(text("SELECT id_empleado FROM survey_responses"))
    existing_ids = set(row[0] for row in result)

# Filtrar solo los que no existen
new_rows = df[~df['id_empleado'].isin(existing_ids)]

if not new_rows.empty:
    new_rows.to_sql(
        "survey_responses", engine, if_exists="append", index=False
    )
    print(f"{len(new_rows)} filas nuevas insertadas correctamente.")
else:
    print("No hay filas nuevas para insertar.")

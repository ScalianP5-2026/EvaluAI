import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "data" / "raw" / "mentors_catalog.xlsx"
CLEAN_PATH = BASE_DIR / "data" / "clean" / "mentors_clean.csv"
ERROR_PATH = BASE_DIR / "data" / "errors" / "mentors_errors.csv"

df = pd.read_excel(RAW_PATH, engine="openpyxl")

# 1. Limpiar espacios y mayúsculas de los encabezados originales
df.columns = df.columns.str.lower().str.strip()

# 2. Renombrar las columnas del PDF a las que espera el sistema
df = df.rename(columns={
    "tutor": "mentor_id",
    "tecnología - módulos individuales de formación": "especialidades"
})


# 3. Crear las columnas faltantes con valores por defecto para evitar el error
if "nombre" not in df.columns:
    df["nombre"] = ""
if "department" not in df.columns:
    df["department"] = "Sin asignar" # Valor por defecto

# A partir de aquí sigue tu código original
expected_columns = [
    "mentor_id",
    "nombre",
    "department",
    "especialidades"
]


missing_columns = [col for col in expected_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Faltan columnas obligatorias: {missing_columns}")

errors = []
valid_rows = []

for _, row in df.iterrows():

    row_errors = []

    if pd.isna(row["mentor_id"]):
        row_errors.append("mentor_id vacío")

    if pd.isna(row["nombre"]):
        row_errors.append("nombre vacío")

    if row_errors:
        error_row = row.copy()
        error_row["errors"] = ", ".join(row_errors)
        errors.append(error_row)

    else:
        valid_rows.append(row)

df["nombre"] = df["nombre"].astype(str).str.strip()
df["department"] = df["department"].astype(str).str.strip()

valid_df = pd.DataFrame(valid_rows)
error_df = pd.DataFrame(errors)

valid_df.to_csv(CLEAN_PATH, index=False)
error_df.to_csv(ERROR_PATH, index=False)

print("Mentors validation completed")
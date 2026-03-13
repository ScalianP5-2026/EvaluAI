import pandas as pd
from pathlib import Path

# Definir las rutas
BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "data" / "raw" / "courses_catalog.xlsx"
CLEAN_PATH = BASE_DIR / "data" / "clean" / "courses_clean.csv"
ERROR_PATH = BASE_DIR / "data" / "errors" / "courses_errors.csv"

# Leer el Excel
df = pd.read_excel(RAW_PATH, engine="openpyxl")

# 1. Normalizar las columnas originales (minúsculas y sin espacios)
df.columns = df.columns.str.lower().str.strip()

# 2. Renombrar las columnas al estándar del sistema
df = df.rename(columns={
    "programas completos": "category",
    "descripcion": "course_name"
})

# 3. Crear columnas faltantes si el sistema las requiere
if "course_id" not in df.columns:
    df["course_id"] = ""

expected_columns = [
    "course_id",
    "course_name",
    "category"
]

# Verificar columnas obligatorias
missing_columns = [col for col in expected_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Faltan columnas obligatorias: {missing_columns}")

errors = []
valid_rows = []

# Analizar fila por fila
for _, row in df.iterrows():

    row_errors = []

    # Validar que el curso tenga nombre
    if pd.isna(row["course_name"]) or str(row["course_name"]).strip() == "":
        row_errors.append("course_name vacío")

    # Validar que el curso tenga categoría asignada
    if pd.isna(row["category"]) or str(row["category"]).strip() == "":
        row_errors.append("category vacía")

    # Clasificar la fila
    if row_errors:
        error_row = row.copy()
        error_row["errors"] = ", ".join(row_errors)
        errors.append(error_row)
    else:
        valid_rows.append(row)

valid_df = pd.DataFrame(valid_rows)
error_df = pd.DataFrame(errors)

# Guardar resultados
valid_df.to_csv(CLEAN_PATH, index=False)
error_df.to_csv(ERROR_PATH, index=False)

print("Courses validation completed")
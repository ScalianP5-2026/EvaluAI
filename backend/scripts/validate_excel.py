import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "data" / "raw" / "survey_raw.xlsx"
CLEAN_PATH = BASE_DIR / "data" / "clean" / "survey_clean.csv"
ERROR_PATH = BASE_DIR / "data" / "errors" / "survey_errors.csv"
REPORT_PATH = BASE_DIR / "data" / "errors" / "validation_report.txt"

df = pd.read_excel(RAW_PATH, engine="openpyxl")

# Normalizar columnas
df.columns = df.columns.str.lower().str.strip()

# Columnas obligatorias según tu dataset
expected_columns = [
    "id_empleado",
    "edad",
    "genero",
    "departamento"
]

missing_columns = [col for col in expected_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Faltan columnas obligatorias: {missing_columns}")

# Detectar duplicados
duplicates = df[df.duplicated(subset=["id_empleado"], keep=False)]

errors = []
valid_rows = []

for _, row in df.iterrows():

    row_errors = []

    if pd.isna(row["id_empleado"]):
        row_errors.append("id_empleado vacío")

    if "edad" in df.columns:
        if pd.notna(row["edad"]) and (row["edad"] < 16 or row["edad"] > 80):
            row_errors.append("edad fuera de rango")

    if row["id_empleado"] in duplicates["id_empleado"].values:
        row_errors.append("id_empleado duplicado")

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

with open(REPORT_PATH, "w") as f:
    f.write("REPORTE VALIDACIÓN\n")
    f.write("-----------------\n")
    f.write(f"Filas totales: {len(df)}\n")
    f.write(f"Filas válidas: {len(valid_df)}\n")
    f.write(f"Filas con error: {len(error_df)}\n")

print("Validación completada")
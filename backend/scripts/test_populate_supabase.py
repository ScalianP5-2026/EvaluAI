import pandas as pd
from sqlalchemy import create_engine, text

# Cambiar con tus credenciales
#DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
DATABASE_URL = "postgresql://postgres.zeoafuemimbvaubaelen:cB6reuDVm3EzJzPG@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)

df = pd.read_excel("backend/data/raw/EIPIA_FO_dataset_100_personas.xls")

# Asegurar que columnas coincidan con nombres SQL
df.columns = df.columns.str.lower()

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
	new_rows.to_sql("survey_responses", engine, if_exists="append", index=False)
	print(f"{len(new_rows)} filas nuevas insertadas correctamente.")
else:
	print("No hay filas nuevas para insertar.")
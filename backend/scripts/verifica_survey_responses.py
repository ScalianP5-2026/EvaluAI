"""
Script de verificación para comprobar que los primeros 100 registros de la tabla survey_responses
fueron actualizados correctamente, especialmente el campo survey_completed_at.

Este script utiliza las variables de entorno SUPABASE_URL y SUPABASE_SERVICE_KEY.
"""
import os

import pandas as pd
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar definidos en el entorno.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Consulta los primeros 100 registros ordenados por id_empleado
data = supabase.table("survey_responses").select("id_empleado,survey_completed_at").order("id_empleado").limit(100).execute()

df = pd.DataFrame(data.data)

print("Primeros 100 registros de survey_responses:")
print(df)

# Verifica el formato de survey_completed_at
def is_iso8601(s):
    try:
        pd.to_datetime(s, format="%Y-%m-%dT%H:%M:%S", errors="raise")
        return True
    except Exception:
        return False

if "survey_completed_at" in df.columns:
    formatos = df["survey_completed_at"].apply(lambda x: is_iso8601(x) if pd.notnull(x) else True)
    if formatos.all():
        print("\nTodos los valores de survey_completed_at están en formato ISO 8601.")
    else:
        print("\nAlgunos valores de survey_completed_at NO están en formato ISO 8601:")
        print(df.loc[~formatos, ["id_empleado", "survey_completed_at"]])
else:
    print("\nNo se encontró la columna survey_completed_at en los resultados.")

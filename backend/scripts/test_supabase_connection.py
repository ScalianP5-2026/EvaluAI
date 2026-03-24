"""
Quick script to test Supabase DB connection and fetch employees table.
"""
import os

from dotenv import load_dotenv
from supabase import create_client

# Cargar variables del .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_KEY not set in environment.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    result = supabase.table("employees").select("*").limit(5).execute()
    print(f"✅ Conexión exitosa. Primeros empleados:")
    for row in result.data:
        print(row)
    if not result.data:
        print("⚠️ La tabla employees está vacía.")
except Exception as e:
    print(f"❌ Error al acceder a Supabase: {e}")

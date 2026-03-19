"""
Employees Seed: Inserta empleados desde CSV en Supabase
"""

import asyncio
import logging
from pathlib import Path

from supabase import Client

logger = logging.getLogger(__name__)

async def seed_employees(supabase: Client) -> bool:
    """
    Lee empleados del CSV y los inserta en la tabla employees.
    Maneja duplicados gracefully (no falla si el empleado ya existe).
    
    Args:
        supabase: Cliente inicializado de Supabase
        
    Returns:
        True si se insertaron todos o parcialmente; False si hay error crítico
    """
    
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "survey_raw.xlsx"
    
    if not data_path.exists():
        logger.error(f"Dataset file not found: {data_path}")
        return False
    
    employees = []
    errors = []
    
    try:
        logger.info(f"Reading employees from dataset: {data_path}")
        
        import pandas as pd
        df = pd.read_excel(data_path, engine="openpyxl")
        
        if df.empty:
            logger.error("Dataset file is empty or malformed")
            return False
        
        logger.info(f"Dataset columns: {list(df.columns)}")
        records = df.to_dict(orient='records')
        
        for row_num, row in enumerate(records, start=2):
            try:
                employee = {
                    "employee_id": str(row.get('id_empleado', '')).strip(),
                    "age": int(row.get('edad', 0)) if row.get('edad') else None,
                    "gender": str(row.get('genero', '')).strip() or None,
                    "department": str(row.get('departamento', '')).strip() or None,
                    "years_in_company": int(row.get('antiguedad_empresa', 0)) if row.get('antiguedad_empresa') else None,
                    "education_level": str(row.get('nivel_educativo', '')).strip() or None,
                }
                
                if not employee['employee_id']:
                    errors.append(f"Row {row_num}: Missing employee_id")
                    continue
                
                employees.append(employee)
            
            except ValueError as e:
                errors.append(f"Row {row_num}: Invalid data type - {e}")
                continue
            except Exception as e:
                errors.append(f"Row {row_num}: Unexpected error - {e}")
                continue
                
        if not employees:
            logger.error("No valid employees found in dataset")
            return False
        
        logger.info(f"Loaded {len(employees)} employees from dataset")
        
        if errors:
            logger.warning(f"Errors during dataset parsing ({len(errors)}): {errors[:5]}")
            
        logger.info(f"Inserting {len(employees)} employees into Supabase...")
                    
        response = supabase.table("employees").insert(employees).execute()
        
        if response.data:
            logger.info(f"✓ Inserted {len(response.data)} employees successfully")
            return True
        else:
            if hasattr(response, 'status_code') and response.status_code == 409:
                logger.info(f"✓ Some/all employees already exist (duplicate key)")
                inserted_count = 0
                
                for employee in employees:
                    try:
                        result = supabase.table("employees").insert([employee]).execute()
                        if result.data:
                            inserted_count += 1
                    except Exception as e:
                        if "duplicate" in str(e).lower() or "409" in str(e):
                            continue
                        else:
                            logger.warning(f"Error inserting {employee['employee_id']}: {e}")                    
                            
                logger.info(f"✓ Inserted {inserted_count} new employees (others were duplicates)")
                return True
            else:
                logger.warning(f"Insert returned unexpected response: {response}")
                return False
            
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {data_path}")
        return False
    except Exception as e:
        # If it's a duplicate key error, that's ok - employees already exist
        if "duplicate" in str(e).lower() or "23505" in str(e):
            logger.info(f"✓ All employees already exist in database (duplicates skipped)")
            return True
        else:
            logger.error(f"Error seeding employees: {e}")
            return False
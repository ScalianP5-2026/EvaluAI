"""
Employees Seed: Inserta empleados desde CSV en Supabase
"""

import asyncio
import csv
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
    
    current = Path(__file__).resolve()
    csv_path = None
    for parent in [current] + list(current.parents):
        candidate = parent / "data" / "raw" / "EIPIA_FO_dataset_100_personas.csv"
        if candidate.exists():
            csv_path = candidate
            break

    if not csv_path:
        logger.error("CSV file not found in any parent data/raw/ directory")
        return False
    
    employees = []
    errors = []
    
    try:
        logger.info(f"Reading employees from CSV: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            
            if reader.fieldnames is None:
                logger.error("CSV file is empty or malformed")
                return False
            
            logger.info(f"CSV columns: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    employee = {
                        "employee_id": row.get('id_empleado', '').strip(),
                        "age": int(row.get('edad', 0)) if row.get('edad') else None,
                        "gender": row.get('genero', '').strip() or None,
                        "department": row.get('departamento', '').strip() or None,
                        "years_in_company": int(row.get('antiguedad_empresa', 0)) if row.get('antiguedad_empresa') else None,
                        "education_level": row.get('nivel_educativo', '').strip() or None,
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
            logger.error("No valid employees found in CSV")
            return False
        
        logger.info(f"Loaded {len(employees)} employees from CSV")
        
        if errors:
            logger.warning(f"Errors during CSV parsing ({len(errors)}): {errors[:5]}")
            
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
        logger.error(f"CSV file not found: {csv_path}")
        return False
    except Exception as e:
        # If it's a duplicate key error, that's ok - employees already exist
        if "duplicate" in str(e).lower() or "23505" in str(e):
            logger.info(f"✓ All employees already exist in database (duplicates skipped)")
            return True
        else:
            logger.error(f"Error seeding employees: {e}")
            return False
"""Generic data upload endpoints that execute ingestion scripts by dataset type."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api/v1/upload", tags=["data-upload"])

BASE_DIR = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = BASE_DIR / "scripts"

UPLOAD_CONFIG: dict[str, dict[str, object]] = {
    "mentors": {
        "script": "load_mentors.py",
        "extensions": {".csv"},
    },
    "courses": {
        "script": "load_courses.py",
        "extensions": {".csv"},
    },
    "employees": {
        "script": "load_employees.py",
        "extensions": {".xlsx", ".xls", ".csv"},
    },
    "survey-answers": {
        "script": "load_survey_answers.py",
        "extensions": {".xlsx", ".xls", ".csv"},
    },
}


def _validate_file(dataset_type: str, file: UploadFile, content: bytes) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="El archivo debe tener nombre")

    extension = Path(file.filename).suffix.lower()
    allowed_extensions = UPLOAD_CONFIG[dataset_type]["extensions"]
    if extension not in allowed_extensions:
        allowed_str = ", ".join(sorted(allowed_extensions))
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido para {dataset_type}. Formatos permitidos: {allowed_str}",
        )

    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo de 10MB")

    return extension


def _run_script(script_name: str, temp_file_path: str) -> tuple[int, str, str]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise HTTPException(status_code=500, detail=f"No se encontró el script: {script_name}")

    env = os.environ.copy()
    env["EVALUAI_INPUT_FILE"] = temp_file_path

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPTS_DIR),
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        check=False,
    )

    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


async def _process_dataset_upload(dataset_type: str, file: UploadFile) -> dict[str, str]:
    if dataset_type not in UPLOAD_CONFIG:
        raise HTTPException(status_code=404, detail=f"Tipo de dataset no soportado: {dataset_type}")

    content = await file.read()
    extension = _validate_file(dataset_type, file, content)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        script_name = str(UPLOAD_CONFIG[dataset_type]["script"])
        return_code, stdout, stderr = _run_script(script_name, temp_path)

        if return_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Error ejecutando {script_name}",
                    "stdout": stdout[-2000:],
                    "stderr": stderr[-2000:],
                },
            )

        return {
            "message": f"Carga completada para {dataset_type}",
            "dataset_type": dataset_type,
            "filename": file.filename,
            "script": script_name,
            "stdout": stdout[-2000:],
            "stderr": stderr[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Tiempo de ejecución excedido para {dataset_type}: {exc}",
        ) from exc
    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


@router.post("/mentors")
async def upload_mentors(file: UploadFile = File(...)) -> dict[str, str]:
    return await _process_dataset_upload("mentors", file)


@router.post("/courses")
async def upload_courses(file: UploadFile = File(...)) -> dict[str, str]:
    return await _process_dataset_upload("courses", file)


@router.post("/employees")
async def upload_employees(file: UploadFile = File(...)) -> dict[str, str]:
    return await _process_dataset_upload("employees", file)


@router.post("/survey-answers")
async def upload_survey_answers(file: UploadFile = File(...)) -> dict[str, str]:
    return await _process_dataset_upload("survey-answers", file)

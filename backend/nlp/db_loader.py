"""Load survey_responses from Supabase into a pandas DataFrame for NLP processing.

This module provides the DB-backed data source for the NLP pipeline,
replacing the legacy CSV-based loading.  When the database is unreachable
it returns ``None`` so the caller can fall back to the static CSV.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Columns required from the survey_responses table for NLP analysis.
_SELECT_COLUMNS = (
    "id_empleado,"
    "departamento,"
    "wave,"
    "survey_completed_at,"
    "open_positive_experience,"
    "open_difficulties_and_training_needs,"
    "c1_confio_sin_verificar,"
    "c2_dificil_sin_ia,"
    "c3_pensamiento_critico,"
    "c4_reflexiono_calidad,"
    "m1_estimulante,"
    "m2_aumenta_interes,"
    "m3_aporta_valor,"
    "m4_mayor_esfuerzo,"
    "frecuencia_uso_ia,"
    "herramienta_principal,"
    "nivel_integracion_ia,"
    "campaign_id"
)


def _get_supabase_client() -> Any | None:
    """Import and return the shared Supabase client, or None on failure."""
    try:
        from backend.app.config import get_supabase_client
        return get_supabase_client()
    except ImportError:
        pass
    try:
        from app.config import get_supabase_client  # type: ignore[no-redef]
        return get_supabase_client()
    except ImportError:
        pass
    logger.warning("Could not import get_supabase_client — DB loading disabled.")
    return None


def load_survey_responses() -> pd.DataFrame | None:
    """Fetch all survey_responses rows from Supabase and return as DataFrame.

    Returns ``None`` when the database cannot be reached or the query fails,
    allowing the caller to fall back to the static CSV.
    """
    client = _get_supabase_client()
    if client is None:
        return None

    try:
        # Supabase REST API paginates at 1000 by default; set a high limit
        # to ensure all rows come back in one round-trip.
        response = client.table("survey_responses").select(_SELECT_COLUMNS).limit(5000).execute()
        rows: list[dict[str, Any]] = response.data or []
        if not rows:
            logger.warning("survey_responses table returned 0 rows.")
            return None

        df = pd.DataFrame(rows)
        logger.info("Loaded %d survey_responses rows from Supabase.", len(df))
        return df

    except Exception as exc:
        logger.warning("Failed to load survey_responses from Supabase: %s", exc)
        return None

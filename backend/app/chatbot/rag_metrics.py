"""
Minimal evaluation loop storage for hybrid RAG.

Stores retrieval/ranking snapshots as JSONL events for offline analysis.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def record_hybrid_rag_event(event: Dict[str, Any]) -> None:
    """
    Persist a single hybrid RAG event in backend/data/processed/hybrid_rag_events.jsonl.
    """
    try:
        output_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "processed"
            / "hybrid_rag_events.jsonl"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            **(event or {}),
        }
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("Could not persist hybrid RAG event: %s", exc)

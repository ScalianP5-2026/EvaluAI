"""
Purge employee-related data from Supabase while keeping app master data.

What it removes:
- survey responses and upload logs
- employee records and user credentials
- chat history/recommendation events linked to employees

What it keeps:
- courses, mentores, campaigns, and other static app metadata

Usage:
    python backend/scripts/empty_employee_data.py --yes
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

from dotenv import load_dotenv
from supabase import create_client


def _delete_all(table: str, filter_column: str, sentinel_value):
    response = (
        supabase.table(table)
        .delete()
        .neq(filter_column, sentinel_value)
        .execute()
    )
    deleted_rows = len(response.data or [])
    print(f"- {table}: {deleted_rows} rows deleted")


def purge_employee_related_data() -> None:
    # Ordered to avoid common FK violations.
    deletion_plan: Iterable[tuple[str, str, object]] = [
        ("chat_turns", "session_id", "00000000-0000-0000-0000-000000000000"),
        ("recommendation_events", "employee_id", "__never__"),
        ("chat_sessions", "employee_id", "__never__"),
        ("import_batch_errors", "row_number", -999999999),
        ("import_batches", "import_type", "__never__"),
        ("survey_responses", "id_empleado", "__never__"),
        ("user_credentials", "employee_id", "__never__"),
        ("employees", "employee_id", "__never__"),
    ]

    print("Starting employee-data purge...")
    for table, filter_column, sentinel in deletion_plan:
        try:
            _delete_all(table, filter_column, sentinel)
        except Exception as exc:
            print(f"! {table}: skipped ({exc})")
    print("Purge complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Empty employee-related data from Supabase")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive purge",
    )
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to run without --yes")

    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise SystemExit("SUPABASE_URL and SUPABASE_KEY are required")

    supabase = create_client(supabase_url, supabase_key)
    purge_employee_related_data()

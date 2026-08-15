"""Persistent history for completed maintenance work orders."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sqlite3

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATABASE_PATH = DATA_DIR / "facilityops.db"
HISTORY_COLUMNS = [
    "Work order",
    "Product ID",
    "Machine type",
    "Maintenance task",
    "Technician",
    "Completed on",
    "Completion notes",
]


def _connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def _ensure_table() -> None:
    with _connection() as connection:
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS maintenance_history (
                work_order_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                maintenance_task TEXT NOT NULL,
                technician TEXT NOT NULL,
                completed_on TEXT NOT NULL,
                completion_notes TEXT NOT NULL
            )'''
        )


def record_completed_work_order(work_order: pd.Series, completion_notes: str = "") -> bool:
    """Record a completed work order once; return whether a history row was added."""
    _ensure_table()
    with _connection() as connection:
        cursor = connection.execute(
            '''INSERT OR IGNORE INTO maintenance_history (
                work_order_id, product_id, machine_type, maintenance_task,
                technician, completed_on, completion_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                work_order["ID"],
                work_order["Product ID"],
                work_order["Machine Type"],
                work_order["Issue"],
                work_order["Assigned To"],
                date.today().isoformat(),
                completion_notes.strip(),
            ),
        )
    return cursor.rowcount == 1


def load_maintenance_history() -> pd.DataFrame:
    """Load completed maintenance records, newest first."""
    _ensure_table()
    with _connection() as connection:
        history = pd.read_sql_query(
            '''SELECT work_order_id AS "Work order", product_id AS "Product ID",
                      machine_type AS "Machine type", maintenance_task AS "Maintenance task",
                      technician AS "Technician", completed_on AS "Completed on",
                      completion_notes AS "Completion notes"
               FROM maintenance_history ORDER BY completed_on DESC, work_order_id DESC''',
            connection,
        )
    return history.reindex(columns=HISTORY_COLUMNS, fill_value="").fillna("")

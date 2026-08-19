"""Persistent checklists for preventive-maintenance schedules."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATABASE_PATH = DATA_DIR / "facilityops.db"


def _connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def _ensure_table() -> None:
    with _connection() as connection:
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS maintenance_checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id TEXT NOT NULL,
                step_order INTEGER NOT NULL,
                checklist_item TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                UNIQUE(schedule_id, step_order)
            )'''
        )


def default_checklist(task: str) -> pd.DataFrame:
    """Create a practical starter checklist for a maintenance task."""
    return pd.DataFrame(
        {
            "Checklist item": [
                "Confirm the machine is safely isolated before maintenance.",
                f"Inspect the components related to: {task}",
                "Perform the required maintenance and record any parts used.",
                "Test normal machine operation and document the outcome.",
            ],
            "Complete": [False, False, False, False],
        }
    )


def load_checklist(schedule_id: str) -> pd.DataFrame:
    """Load one schedule's checklist, returning an empty frame if none exists."""
    _ensure_table()
    with _connection() as connection:
        checklist = pd.read_sql_query(
            'SELECT checklist_item AS "Checklist item", completed AS "Complete" '
            'FROM maintenance_checklists WHERE schedule_id = ? ORDER BY step_order',
            connection,
            params=(schedule_id,),
        )
    if checklist.empty:
        return pd.DataFrame({"Checklist item": pd.Series(dtype="string"), "Complete": pd.Series(dtype="bool")})
    checklist["Complete"] = checklist["Complete"].astype(bool)
    return checklist


def delete_checklist(schedule_id: str) -> None:
    """Remove a schedule's saved checklist."""
    _ensure_table()
    with _connection() as connection:
        connection.execute("DELETE FROM maintenance_checklists WHERE schedule_id = ?", (schedule_id,))


def save_checklist(schedule_id: str, checklist: pd.DataFrame) -> None:
    """Replace a schedule's checklist with its current saved completion state."""
    _ensure_table()
    cleaned = checklist[["Checklist item", "Complete"]].copy().fillna({"Checklist item": "", "Complete": False})
    with _connection() as connection:
        connection.execute("DELETE FROM maintenance_checklists WHERE schedule_id = ?", (schedule_id,))
        connection.executemany(
            '''INSERT INTO maintenance_checklists (schedule_id, step_order, checklist_item, completed)
               VALUES (?, ?, ?, ?)''',
            [
                (schedule_id, step_number, row["Checklist item"].strip(), int(bool(row["Complete"])))
                for step_number, (_, row) in enumerate(cleaned.iterrows(), start=1)
                if row["Checklist item"].strip()
            ],
        )

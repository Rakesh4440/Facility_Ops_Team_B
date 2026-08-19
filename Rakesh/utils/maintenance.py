"""Preventive-maintenance schedule helpers with local SQLite persistence."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


SCHEDULE_COLUMNS = [
    "Schedule ID",
    "Product ID",
    "Machine Type",
    "Maintenance Task",
    "Frequency",
    "Assigned To",
    "Next Due Date",
    "Active",
]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATABASE_PATH = DATA_DIR / "facilityops.db"
TABLE_NAME = "maintenance_schedules"


def _connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def _starter_schedules() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["PM-1001", "M14860", "M", "Inspect spindle vibration", "Monthly", "A. Sharma", "2026-08-05", "Yes"],
            ["PM-1002", "L47181", "L", "Lubricate cutting assembly", "Weekly", "R. Patel", "2026-08-03", "Yes"],
            ["PM-1003", "H29424", "H", "Check heat dissipation", "Quarterly", "K. Singh", "2026-09-15", "Yes"],
        ],
        columns=SCHEDULE_COLUMNS,
    )


def _ensure_database() -> None:
    with _connection() as connection:
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS maintenance_schedules (
                "Schedule ID" TEXT PRIMARY KEY,
                "Product ID" TEXT NOT NULL,
                "Machine Type" TEXT NOT NULL,
                "Maintenance Task" TEXT NOT NULL,
                "Frequency" TEXT NOT NULL,
                "Assigned To" TEXT NOT NULL,
                "Next Due Date" TEXT NOT NULL,
                "Active" TEXT NOT NULL
            )'''
        )
        count = connection.execute("SELECT COUNT(*) FROM maintenance_schedules").fetchone()[0]
        if not count:
            _starter_schedules().to_sql(TABLE_NAME, connection, if_exists="append", index=False)


def load_schedules() -> pd.DataFrame:
    """Load preventive-maintenance schedules ordered by their due date."""
    _ensure_database()
    with _connection() as connection:
        schedules = pd.read_sql_query(
            'SELECT "Schedule ID", "Product ID", "Machine Type", "Maintenance Task", '
            '"Frequency", "Assigned To", "Next Due Date", "Active" '
            'FROM maintenance_schedules ORDER BY "Next Due Date", "Schedule ID"',
            connection,
        )
    return schedules.fillna("").reindex(columns=SCHEDULE_COLUMNS, fill_value="")


def save_schedules(schedules: pd.DataFrame) -> None:
    """Persist maintenance schedules to the local SQLite database."""
    _ensure_database()
    cleaned = schedules.reindex(columns=SCHEDULE_COLUMNS).fillna("")
    with _connection() as connection:
        cleaned.to_sql(TABLE_NAME, connection, if_exists="replace", index=False)
        connection.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_maintenance_schedules_id '
            'ON maintenance_schedules ("Schedule ID")'
        )


def next_schedule_id(schedules: pd.DataFrame) -> str:
    """Generate the next sequential preventive-maintenance identifier."""
    numbers = schedules["Schedule ID"].str.extract(r"PM-(\d+)", expand=False).dropna()
    next_number = numbers.astype(int).max() + 1 if not numbers.empty else 1001
    return f"PM-{next_number}"

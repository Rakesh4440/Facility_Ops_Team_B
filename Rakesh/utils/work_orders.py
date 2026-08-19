"""Shared work-order helpers with local SQLite persistence."""

from pathlib import Path
import sqlite3

import pandas as pd


WORK_ORDER_COLUMNS = [
    "ID",
    "Product ID",
    "Machine Type",
    "Issue",
    "Priority",
    "Assigned To",
    "Due Date",
    "Status",
]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
WORK_ORDER_DB_PATH = DATA_DIR / "facilityops.db"
LEGACY_WORK_ORDERS_PATH = DATA_DIR / "work_orders.csv"
TABLE_NAME = "work_orders"


def initial_work_orders() -> pd.DataFrame:
    """Return the starter work orders used for a first-time installation."""
    return pd.DataFrame(
        [
            ["WO-1001", "M14860", "M", "Inspect spindle vibration", "High", "A. Sharma", "2026-07-18", "Open"],
            ["WO-1002", "L47181", "L", "Replace worn cutting tool", "Medium", "R. Patel", "2026-07-20", "In Progress"],
            ["WO-1003", "H29424", "H", "Review heat dissipation", "High", "K. Singh", "2026-07-17", "Open"],
            ["WO-1004", "L50962", "L", "Complete preventive inspection", "Low", "P. Das", "2026-07-22", "Completed"],
        ],
        columns=WORK_ORDER_COLUMNS,
    )


def _connection() -> sqlite3.Connection:
    """Open the application's local SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(WORK_ORDER_DB_PATH)


def _ensure_database() -> None:
    """Create the database and safely migrate the previous CSV once, if present."""
    with _connection() as connection:
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS work_orders (
                "ID" TEXT PRIMARY KEY,
                "Product ID" TEXT NOT NULL,
                "Machine Type" TEXT NOT NULL,
                "Issue" TEXT NOT NULL,
                "Priority" TEXT NOT NULL,
                "Assigned To" TEXT NOT NULL,
                "Due Date" TEXT NOT NULL,
                "Status" TEXT NOT NULL
            )'''
        )
        count = connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0]
        if count:
            return

        if LEGACY_WORK_ORDERS_PATH.exists():
            work_orders = pd.read_csv(LEGACY_WORK_ORDERS_PATH, dtype=str).fillna("")
            work_orders = work_orders.reindex(columns=WORK_ORDER_COLUMNS, fill_value="")
        else:
            work_orders = initial_work_orders()
        work_orders.to_sql(TABLE_NAME, connection, if_exists="append", index=False)


def load_work_orders() -> pd.DataFrame:
    """Load all persisted work orders from the local SQLite database."""
    _ensure_database()
    with _connection() as connection:
        work_orders = pd.read_sql_query(
            'SELECT "ID", "Product ID", "Machine Type", "Issue", "Priority", '
            '"Assigned To", "Due Date", "Status" FROM work_orders ORDER BY "ID"',
            connection,
        )
    return work_orders.fillna("").reindex(columns=WORK_ORDER_COLUMNS, fill_value="")


def save_work_orders(work_orders: pd.DataFrame) -> None:
    """Save the current work-order list to SQLite so it survives app restarts."""
    _ensure_database()
    cleaned_orders = work_orders.reindex(columns=WORK_ORDER_COLUMNS).fillna("")
    with _connection() as connection:
        cleaned_orders.to_sql(TABLE_NAME, connection, if_exists="replace", index=False)
        connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_work_orders_id ON work_orders ("ID")')


def next_work_order_id(work_orders: pd.DataFrame) -> str:
    """Generate the next sequential work-order identifier."""
    existing_numbers = work_orders["ID"].str.extract(r"WO-(\d+)", expand=False).dropna()
    next_number = existing_numbers.astype(int).max() + 1 if not existing_numbers.empty else 1001
    return f"WO-{next_number}"


def preventive_work_order_exists(schedule_id: str) -> bool:
    """Return whether a preventive work order was already generated for a schedule."""
    work_orders = load_work_orders()
    schedule_marker = f"Preventive maintenance [{schedule_id}]"
    return work_orders["Issue"].str.startswith(schedule_marker, na=False).any()


def generate_preventive_work_order(schedule: pd.Series) -> str | None:
    """Create one open work order from a preventive-maintenance schedule.

    Returns the new work-order ID, or ``None`` when the schedule already has one.
    """
    schedule_id = str(schedule["Schedule ID"])
    if preventive_work_order_exists(schedule_id):
        return None

    work_orders = load_work_orders()
    new_id = next_work_order_id(work_orders)
    new_order = pd.DataFrame(
        [[
            new_id,
            schedule["Product ID"],
            schedule["Machine Type"],
            f"Preventive maintenance [{schedule_id}]: {schedule['Maintenance Task']}",
            "Medium",
            schedule["Assigned To"],
            schedule["Next Due Date"],
            "Open",
        ]],
        columns=WORK_ORDER_COLUMNS,
    )
    save_work_orders(pd.concat([work_orders, new_order], ignore_index=True))
    return new_id

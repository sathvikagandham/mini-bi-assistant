"""
Database layer.

Public functions:
  - init_db(df)            : create sales.db from scratch and insert rows
  - get_readonly_connection(): open the DB with mode=ro (writes fail)
  - row_count()            : convenience for tests and the init script
"""
from pathlib import Path
from urllib.parse import quote
import sqlite3

import pandas as pd

from app import config


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sales (
    transaction_id   TEXT    PRIMARY KEY,
    order_date       DATE    NOT NULL,
    product          TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    region           TEXT    NOT NULL,
    sales_channel    TEXT    NOT NULL,
    quantity         INTEGER NOT NULL,
    unit_price       REAL    NOT NULL,
    discount_amount  REAL    NOT NULL DEFAULT 0,
    status           TEXT    NOT NULL,
    revenue          REAL    NOT NULL
);
"""

INSERT_SQL = """
INSERT INTO sales (
    transaction_id, order_date, product, category, region,
    sales_channel, quantity, unit_price, discount_amount, status, revenue
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# Column order MUST match the INSERT_SQL placeholder order
COLUMN_ORDER = [
    "transaction_id", "order_date", "product", "category", "region",
    "sales_channel", "quantity", "unit_price", "discount_amount",
    "status", "revenue",
]


def init_db(df: pd.DataFrame, db_path: Path | None = None) -> Path:
    """
    Create (or recreate) the SQLite database at db_path,
    then insert every row of df into the sales table.
    Returns the path to the created file.
    """
    if db_path is None:
        db_path = config.DB_PATH

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # start clean every run

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(CREATE_TABLE_SQL)

        # Convert datetime column to ISO string for SQLite storage
        df_insert = df.copy()
        df_insert["order_date"] = df_insert["order_date"].dt.strftime("%Y-%m-%d")

        # itertuples(name=None) returns plain tuples in column order
        rows = df_insert[COLUMN_ORDER].itertuples(index=False, name=None)
        conn.executemany(INSERT_SQL, rows)
        conn.commit()
    finally:
        conn.close()

    return db_path


def get_readonly_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Open the DB in READ-ONLY mode using a SQLite URI.
    Any INSERT/UPDATE/DELETE against this connection will raise an error.
    """
    if db_path is None:
        db_path = config.DB_PATH

    # URL-encode the path (spaces → %20) and add ?mode=ro
    # safe="/:" keeps the drive-letter colon and path slashes intact
    db_uri = "file:" + quote(db_path.resolve().as_posix(), safe="/:") + "?mode=ro"
    return sqlite3.connect(db_uri, uri=True)


def row_count(db_path: Path | None = None) -> int:
    """Return the number of rows in the sales table."""
    conn = get_readonly_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    finally:
        conn.close()
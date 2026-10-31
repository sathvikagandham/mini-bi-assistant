"""
Data loading and cleaning.

Two public functions:
  - load_raw_csv()    : read the CSV into a DataFrame (no cleaning)
  - clean_data()      : apply the 8-step cleaning pipeline

Also exposes load_and_clean() for convenience.
"""
from pathlib import Path

import pandas as pd

from app import config
from app.analytics import calculate_revenue


# Maps raw CSV column names → snake_case names used by the DB schema.
RENAME_MAP = {
    "Transaction_Id":  "transaction_id",
    "Order_date":      "order_date",
    "Product":         "product",
    "Category":        "category",
    "Region":          "region",
    "Sales_channel":   "sales_channel",
    "Quantity":        "quantity",
    "Unit_price":      "unit_price",
    "Discount_amount": "discount_amount",
    "Status":          "status",
}

# String columns where we strip surrounding whitespace.
STRING_COLUMNS = ["Product", "Category", "Region", "Sales_channel", "Status"]


def load_raw_csv(path: Path | None = None) -> pd.DataFrame:
    """Step 1: read the CSV file into a DataFrame. No cleaning yet."""
    if path is None:
        path = config.CSV_PATH
    # utf-8-sig handles both UTF-8 and UTF-8-with-BOM files
    return pd.read_csv(path, encoding="utf-8-sig")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the 8-step cleaning pipeline.

    Input:  raw DataFrame loaded by load_raw_csv()  (51 rows)
    Output: clean DataFrame ready for DB insertion  (48 rows)
    """
    df = df.copy()  # do not mutate the caller's DataFrame

    # -- Step 2: parse Order_date with explicit DD-MM-YYYY --
    # Never let pandas guess: the format is unambiguous here.
    df["Order_date"] = pd.to_datetime(
        df["Order_date"], format="%d-%m-%Y", errors="coerce"
    )

    # -- Step 3: strip whitespace from string columns --
    for col in STRING_COLUMNS:
        df[col] = df[col].astype(str).str.strip()

    # -- Step 4: drop rows with unparseable dates (NaT) --
    df = df.dropna(subset=["Order_date"])

    # -- Step 5: drop rows with missing unit price --
    df = df.dropna(subset=["Unit_price"])

    # -- Step 6: drop returned orders --
    df = df[df["Status"] != "Returned"]

    # -- Step 7: drop rows with zero or negative quantity --
    df = df[df["Quantity"] > 0]

    # -- Step 8: compute revenue + rename columns to snake_case --
    # calculate_revenue() works on Series too — one formula, one place.
    df["revenue"] = calculate_revenue(
        df["Quantity"], df["Unit_price"], df["Discount_amount"]
    )
    df = df.rename(columns=RENAME_MAP)

    return df.reset_index(drop=True)


def load_and_clean(path: Path | None = None) -> pd.DataFrame:
    """Convenience wrapper: load + clean in one call."""
    return clean_data(load_raw_csv(path))
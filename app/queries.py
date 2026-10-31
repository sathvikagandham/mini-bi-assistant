"""
Pre-written SQL for each supported intent.

Design:
  - Each intent has ONE SQL string, stored as a constant.
  - INTENT_SQL maps intent label → SQL string.
  - run_query(conn, intent, params) is the single dispatcher.
  - All SQL is read-only (SELECT only). No user input goes into the SQL
    string itself — parameters always go through ? placeholders.
"""
import re
import sqlite3


# --- Intent 1: total revenue ---
TOTAL_REVENUE_SQL = """
SELECT
    SUM(revenue)  AS total_revenue,
    COUNT(*)      AS transaction_count,
    AVG(revenue)  AS average_revenue
FROM sales;
"""


# --- Intent 2: top product by revenue ---
TOP_PRODUCT_SQL = """
SELECT
    product,
    SUM(revenue)  AS total_revenue,
    SUM(quantity) AS total_quantity,
    COUNT(*)      AS transaction_count
FROM sales
GROUP BY product
ORDER BY total_revenue DESC;
"""


# --- Intent 3: monthly revenue trend ---
MONTHLY_TREND_SQL = """
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(revenue)                  AS total_revenue,
    COUNT(*)                      AS transaction_count
FROM sales
GROUP BY month
ORDER BY month ASC;
"""


# --- Intent 4: top region by revenue ---
TOP_REGION_SQL = """
SELECT
    region,
    SUM(revenue)  AS total_revenue,
    SUM(quantity) AS total_quantity,
    COUNT(*)      AS transaction_count
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;
"""


# --- Intent 5: compare two months ---
# Takes 2 params: month_a, month_b in 'YYYY-MM' format.
MONTH_COMPARISON_SQL = """
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(revenue)                  AS total_revenue,
    COUNT(*)                      AS transaction_count
FROM sales
WHERE strftime('%Y-%m', order_date) IN (?, ?)
GROUP BY month
ORDER BY month ASC;
"""


INTENT_SQL = {
    "total_revenue":    TOTAL_REVENUE_SQL,
    "top_product":      TOP_PRODUCT_SQL,
    "monthly_trend":    MONTHLY_TREND_SQL,
    "top_region":       TOP_REGION_SQL,
    "month_comparison": MONTH_COMPARISON_SQL,
}


# Regex for validating 'YYYY-MM' format (used only by month_comparison)
_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def run_query(
    conn: sqlite3.Connection,
    intent: str,
    params: dict | None = None,
) -> list[tuple]:
    """
    Execute the SQL for the given intent and return raw rows.

    Raises ValueError on:
      - unknown intent
      - missing/invalid params for month_comparison
    """
    if intent not in INTENT_SQL:
        raise ValueError(f"Unknown intent: {intent!r}")

    sql = INTENT_SQL[intent]

    if intent == "month_comparison":
        params = params or {}
        month_a = params.get("month_a")
        month_b = params.get("month_b")
        if not month_a or not month_b:
            raise ValueError(
                "month_comparison requires both 'month_a' and 'month_b' params"
            )
        for m in (month_a, month_b):
            if not _MONTH_PATTERN.match(m):
                raise ValueError(
                    f"Invalid month format: {m!r} — expected 'YYYY-MM', e.g. '2026-03'"
                )
        return conn.execute(sql, (month_a, month_b)).fetchall()

    return conn.execute(sql).fetchall()
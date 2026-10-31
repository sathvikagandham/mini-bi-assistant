"""
Run all 5 intents and print the results.

Run:
    python scripts/verify_queries.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_readonly_connection
from app.queries import run_query


def main() -> int:
    conn = get_readonly_connection()
    try:
        # --- 1. Total revenue ---
        rows = run_query(conn, "total_revenue")
        total, txn_count, avg = rows[0]
        print("[1] TOTAL REVENUE")
        print(f"    Total:         ₹{total:,.2f}")
        print(f"    Transactions:  {txn_count}")
        print(f"    Average:       ₹{avg:,.2f}")

        # --- 2. Top product ---
        rows = run_query(conn, "top_product")
        print("\n[2] REVENUE BY PRODUCT (highest first)")
        for r in rows:
            print(f"    {r[0]:<16} ₹{r[1]:>12,.2f}  ({r[2]:>3} units, {r[3]:>2} txns)")

        # --- 3. Monthly trend ---
        rows = run_query(conn, "monthly_trend")
        print("\n[3] MONTHLY REVENUE TREND")
        for r in rows:
            print(f"    {r[0]}  ₹{r[1]:>12,.2f}  ({r[2]:>2} txns)")

        # --- 4. Top region ---
        rows = run_query(conn, "top_region")
        print("\n[4] REVENUE BY REGION (highest first)")
        for r in rows:
            print(f"    {r[0]:<8} ₹{r[1]:>12,.2f}  ({r[2]:>3} units, {r[3]:>2} txns)")

        # --- 5. Month comparison ---
        rows = run_query(
            conn,
            "month_comparison",
            {"month_a": "2026-01", "month_b": "2026-06"},
        )
        print("\n[5] MONTH COMPARISON: 2026-01 vs 2026-06")
        if not rows:
            print("    (no data)")
        for r in rows:
            print(f"    {r[0]}  ₹{r[1]:>12,.2f}  ({r[2]:>2} txns)")

        if len(rows) == 2:
            delta = rows[1][1] - rows[0][1]
            pct = (delta / rows[0][1] * 100) if rows[0][1] else 0
            sign = "+" if delta >= 0 else ""
            print(f"    Change: {sign}₹{delta:,.2f}  ({sign}{pct:.2f}%)")

        # --- Guardrail checks (expected to fail) ---
        print("\n[GUARDRAILS]")
        try:
            run_query(conn, "not_a_real_intent")
            print("    ❌ Should have raised for unknown intent")
        except ValueError as e:
            print(f"    ✅ Unknown intent rejected: {e}")

        try:
            run_query(conn, "month_comparison", {"month_a": "2026-13", "month_b": "2026-06"})
            print("    ❌ Should have raised for invalid month format")
        except ValueError as e:
            print(f"    ✅ Invalid month rejected: {e}")

        try:
            run_query(conn, "month_comparison", {"month_a": "2026-01"})
            print("    ❌ Should have raised for missing month_b")
        except ValueError as e:
            print(f"    ✅ Missing param rejected: {e}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
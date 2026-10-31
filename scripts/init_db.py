"""
One-shot script: CSV → clean → SQLite → verify.

Run from project root:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# Add project root to sys.path so 'from app import ...' works
# when this file is run as a script (not as a module).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data_loader import load_and_clean
from app.db import get_readonly_connection, init_db, row_count


EXPECTED_ROWS = 48


def main() -> int:
    print("[1/4] Loading and cleaning CSV...")
    df = load_and_clean()
    print(f"      → Cleaned rows: {len(df)}")

    print("[2/4] Writing to database...")
    db_path = init_db(df)
    print(f"      → Database: {db_path}")

    print("[3/4] Verifying row count...")
    count = row_count()
    print(f"      → Rows in DB: {count}")
    if count != EXPECTED_ROWS:
        print(f"\n❌ ERROR: Expected {EXPECTED_ROWS} rows, found {count}")
        return 1

    print("[4/4] Sample data and total revenue...")
    conn = get_readonly_connection()
    try:
        print("\n  First 5 transactions:")
        for row in conn.execute(
            "SELECT transaction_id, order_date, product, region, revenue "
            "FROM sales ORDER BY transaction_id LIMIT 5"
        ):
            print(
                f"    {row[0]} | {row[1]} | {row[2]:<15} | "
                f"{row[3]:<6} | ₹{row[4]:>10,.2f}"
            )

        total = conn.execute("SELECT SUM(revenue) FROM sales").fetchone()[0]
        print(f"\n  Total revenue: ₹{total:,.2f}")
    finally:
        conn.close()

    print(f"\n✅ SUCCESS: {count} rows inserted into {db_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
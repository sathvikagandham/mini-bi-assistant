"""
Verify that excluded rows are truly absent from the DB.

Run:
    python scripts/verify.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_readonly_connection


EXCLUDED = {
    "TXN0033": "Status = Returned",
    "TXN0034": "Quantity = 0",
    "TXN0051": "Unit_price missing",
}


def main() -> int:
    conn = get_readonly_connection()
    all_ok = True
    try:
        print("Excluded-row check:")
        for tid, reason in EXCLUDED.items():
            found = conn.execute(
                "SELECT 1 FROM sales WHERE transaction_id = ?", (tid,)
            ).fetchone()
            status = "FOUND ❌" if found else "absent ✅"
            print(f"  {tid} ({reason}): {status}")
            if found:
                all_ok = False
    finally:
        conn.close()

    print("\n✅ All exclusions verified" if all_ok else "\n❌ Some exclusions FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
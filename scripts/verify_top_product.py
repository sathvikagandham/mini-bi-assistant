"""Cross-check: top product revenue vs direct SUM for that product."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_readonly_connection
from app.queries import run_query


conn = get_readonly_connection()
top = run_query(conn, "top_product")[0]
direct = conn.execute(
    "SELECT SUM(revenue) FROM sales WHERE product = ?", (top[0],)
).fetchone()[0]
conn.close()

match = abs(top[1] - direct) < 0.01
print(f"Top product:          {top[0]}")
print(f"From top_product query: ₹{top[1]:,.2f}")
print(f"From direct SUM query:  ₹{direct:,.2f}")
print(f"Match: {match}")
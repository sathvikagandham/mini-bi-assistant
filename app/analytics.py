"""
Business logic: revenue calculation.

Assumption (documented in README and AI_USAGE.md):
    discount_amount is a TOTAL order-level discount
    (a lump-sum rupee value for the whole transaction),
    NOT a per-unit discount.

If the business later says it is per-unit, change ONLY this function
and re-run the test suite.
"""


def calculate_revenue(quantity, unit_price, discount_amount):
    """
    Compute revenue for one transaction.

    Works on both:
      - scalars:         calculate_revenue(6, 9500, 500)        → 56500
      - pandas Series:   calculate_revenue(df['qty'], df['price'], df['disc'])
        (Series arithmetic is element-wise, so the same expression
         produces a Series of revenues — no loop required.)

    Formula:
        revenue = (quantity × unit_price) − discount_amount
    """
    return (quantity * unit_price) - discount_amount

# ============================================================
# Answer formatters — turn raw SQL rows into (answer, data, table)
# Each returns a 3-tuple:
#   answer          : str          — human-readable sentence
#   data            : dict         — primary result key-values
#   supporting_table: list[dict] | None — optional breakdown
# ============================================================

def _format_total_revenue(rows):
    total, count, avg = rows[0]
    answer = (
        f"The total revenue is ₹{total:,.2f} across {count} transactions "
        f"(average ₹{avg:,.2f} per transaction)."
    )
    data = {
        "total_revenue": round(total, 2),
        "transaction_count": count,
        "average_revenue": round(avg, 2),
    }
    return answer, data, None


def _format_top_product(rows):
    top = rows[0]
    answer = (
        f"{top[0]} generated the highest revenue at ₹{top[1]:,.2f} "
        f"({top[2]} units sold across {top[3]} transactions)."
    )
    data = {
        "product": top[0],
        "total_revenue": round(top[1], 2),
        "total_quantity": top[2],
        "transaction_count": top[3],
    }
    supporting = [
        {
            "product": r[0],
            "total_revenue": round(r[1], 2),
            "total_quantity": r[2],
            "transaction_count": r[3],
        }
        for r in rows
    ]
    return answer, data, supporting


def _format_monthly_trend(rows):
    if not rows:
        return "No monthly data available.", {}, None

    answer = f"Revenue trend across {len(rows)} months: " + "; ".join(
        f"{r[0]} ₹{r[1]:,.2f}" for r in rows
    ) + "."

    data = {"months": [{"month": r[0], "total_revenue": round(r[1], 2), "transaction_count": r[2]} for r in rows]}
    supporting = data["months"]
    return answer, data, supporting


def _format_top_region(rows):
    top = rows[0]
    answer = (
        f"{top[0]} region generated the highest revenue at ₹{top[1]:,.2f} "
        f"({top[2]} units across {top[3]} transactions)."
    )
    data = {
        "region": top[0],
        "total_revenue": round(top[1], 2),
        "total_quantity": top[2],
        "transaction_count": top[3],
    }
    supporting = [
        {
            "region": r[0],
            "total_revenue": round(r[1], 2),
            "total_quantity": r[2],
            "transaction_count": r[3],
        }
        for r in rows
    ]
    return answer, data, supporting


def _format_month_comparison(rows, params):
    month_a, month_b = params["month_a"], params["month_b"]

    if len(rows) < 2:
        return (
            f"Could not compare {month_a} and {month_b}: one or both months have no data.",
            {"month_a": month_a, "month_b": month_b, "rows": []},
            None,
        )

    # Rows are sorted ascending by month; identify which is which
    by_month = {r[0]: r for r in rows}
    a = by_month.get(month_a)
    b = by_month.get(month_b)

    if not a or not b:
        return (
            f"One of the requested months ({month_a}, {month_b}) has no data.",
            {"month_a": month_a, "month_b": month_b},
            None,
        )

    delta = b[1] - a[1]
    pct = (delta / a[1] * 100) if a[1] else 0.0
    sign = "+" if delta >= 0 else ""
    direction = "increased" if delta > 0 else ("decreased" if delta < 0 else "was unchanged")

    answer = (
        f"Revenue {direction} by ₹{abs(delta):,.2f} ({sign}{pct:.2f}%) "
        f"from {month_a} (₹{a[1]:,.2f}) to {month_b} (₹{b[1]:,.2f})."
    )
    data = {
        "month_a": month_a, "revenue_a": round(a[1], 2),
        "month_b": month_b, "revenue_b": round(b[1], 2),
        "delta": round(delta, 2),
        "percent_change": round(pct, 2),
    }
    supporting = [
        {"month": r[0], "total_revenue": round(r[1], 2), "transaction_count": r[2]}
        for r in rows
    ]
    return answer, data, supporting


def format_answer(intent, rows, params=None):
    """Dispatcher: route to the right formatter. Returns (answer, data, table)."""
    params = params or {}
    if intent == "total_revenue":
        return _format_total_revenue(rows)
    if intent == "top_product":
        return _format_top_product(rows)
    if intent == "monthly_trend":
        return _format_monthly_trend(rows)
    if intent == "top_region":
        return _format_top_region(rows)
    if intent == "month_comparison":
        return _format_month_comparison(rows, params)
    raise ValueError(f"Cannot format intent: {intent}")
"""
Analytics queries against the data warehouse.
All functions return plain Python dicts/lists suitable for JSON or template rendering.
"""

from db_manager import get_conn


# ── Dynamic menu ordering ─────────────────────────────────────────────────────

def category_order_for_slot(time_slot: str) -> list[dict]:
    """
    Return all categories ordered by total quantity sold in the given time slot.
    Categories with no sales appear at the end (alphabetically).
    """
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        """
        SELECT
            dc.category_id,
            dc.category_name,
            COALESCE(SUM(slot_sales.qty), 0)  AS total_qty,
            COALESCE(SUM(slot_sales.rev), 0)  AS total_revenue
        FROM DimCategory dc
        LEFT JOIN DimMenuItem dm ON dm.category_id = dc.category_id
        LEFT JOIN (
            SELECT fs.item_id,
                   SUM(fs.quantity)    AS qty,
                   SUM(fs.total_price) AS rev
            FROM FactSales fs
            JOIN DimTime dt ON dt.time_id = fs.time_id
                            AND dt.time_slot = ?
            GROUP BY fs.item_id
        ) slot_sales ON slot_sales.item_id = dm.item_id
        GROUP BY dc.category_id
        ORDER BY total_qty DESC, dc.category_name ASC
        """,
        (time_slot,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def menu_items_with_sales_for_slot(time_slot: str) -> list[dict]:
    """
    Return all menu items with their sales quantity in the given time slot.
    Useful for popularity-based sorting.
    """
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        """
        SELECT
            dm.item_id,
            dm.item_name,
            dm.price,
            dm.category_id,
            ROUND(dm.price - dm.cost, 2) AS margin,
            ROUND((dm.price - dm.cost) / dm.price * 100, 0) AS margin_pct,
            COALESCE(slot_sales.qty, 0) AS total_qty
        FROM DimMenuItem dm
        LEFT JOIN (
            SELECT fs.item_id,
                   SUM(fs.quantity) AS qty
            FROM FactSales fs
            JOIN DimTime dt ON dt.time_id = fs.time_id
                            AND dt.time_slot = ?
            GROUP BY fs.item_id
        ) slot_sales ON slot_sales.item_id = dm.item_id
        ORDER BY total_qty DESC, dm.item_name ASC
        """,
        (time_slot,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── KPI summary ───────────────────────────────────────────────────────────────

def kpi_summary() -> dict:
    conn = get_conn()
    c = conn.cursor()

    total_revenue = c.execute(
        "SELECT COALESCE(SUM(total_price),0) FROM FactSales"
    ).fetchone()[0]

    total_orders = c.execute(
        "SELECT COUNT(DISTINCT order_id) FROM FactSales"
    ).fetchone()[0]

    total_items_sold = c.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM FactSales"
    ).fetchone()[0]

    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0

    conn.close()
    return {
        "total_revenue":    round(total_revenue, 2),
        "total_orders":     total_orders,
        "total_items_sold": total_items_sold,
        "avg_order_value":  avg_order_value,
    }


# ── Top / bottom sellers ──────────────────────────────────────────────────────

def top_items(limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT dm.item_name,
               dc.category_name,
               SUM(fs.quantity)    AS total_qty,
               SUM(fs.total_price) AS total_revenue,
               ROUND(dm.price - dm.cost, 2) AS margin
        FROM FactSales fs
        JOIN DimMenuItem dm ON dm.item_id = fs.item_id
        JOIN DimCategory dc ON dc.category_id = dm.category_id
        GROUP BY fs.item_id
        ORDER BY total_qty DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def bottom_items(limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT dm.item_name,
               dc.category_name,
               COALESCE(SUM(fs.quantity), 0)    AS total_qty,
               COALESCE(SUM(fs.total_price), 0) AS total_revenue,
               ROUND(dm.price - dm.cost, 2) AS margin
        FROM DimMenuItem dm
        JOIN DimCategory dc ON dc.category_id = dm.category_id
        LEFT JOIN FactSales fs ON fs.item_id = dm.item_id
        GROUP BY dm.item_id
        ORDER BY total_qty ASC, margin DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Category performance ──────────────────────────────────────────────────────

def category_performance() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT dc.category_name,
               COALESCE(SUM(fs.quantity), 0)    AS total_qty,
               COALESCE(SUM(fs.total_price), 0) AS total_revenue
        FROM DimCategory dc
        LEFT JOIN DimMenuItem dm ON dm.category_id = dc.category_id
        LEFT JOIN FactSales   fs ON fs.item_id  = dm.item_id
        GROUP BY dc.category_id
        ORDER BY total_revenue DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Time-slot breakdown ───────────────────────────────────────────────────────

def sales_by_timeslot() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT dt.time_slot,
               dc.category_name,
               SUM(fs.quantity)    AS total_qty,
               SUM(fs.total_price) AS total_revenue
        FROM FactSales fs
        JOIN DimTime     dt ON dt.time_id     = fs.time_id
        JOIN DimMenuItem dm ON dm.item_id     = fs.item_id
        JOIN DimCategory dc ON dc.category_id = dm.category_id
        GROUP BY dt.time_slot, dc.category_id
        ORDER BY dt.time_slot, total_qty DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def sales_by_hour() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT dt.hour,
               SUM(fs.quantity)    AS total_qty,
               SUM(fs.total_price) AS total_revenue
        FROM FactSales fs
        JOIN DimTime dt ON dt.time_id = fs.time_id
        GROUP BY dt.hour
        ORDER BY dt.hour
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Optimization recommendations ─────────────────────────────────────────────

def optimization_recommendations() -> list[dict]:
    """
    Rule-based recommendations derived from the warehouse data.
    Each (type, item) pair appears at most once.
    """
    conn = get_conn()
    c = conn.cursor()

    recs = []
    seen: set[tuple] = set()  # (type, item_name)

    def _add(rec: dict):
        key = (rec["type"], rec["item"])
        if key not in seen:
            seen.add(key)
            recs.append(rec)

    # 1. High margin, low sales → promote
    rows = c.execute(
        """
        SELECT dm.item_name, dc.category_name,
               COALESCE(SUM(fs.quantity), 0)               AS qty,
               ROUND(dm.price - dm.cost, 2)                 AS margin,
               ROUND((dm.price-dm.cost)/dm.price*100, 1)    AS margin_pct
        FROM DimMenuItem dm
        JOIN DimCategory dc ON dc.category_id = dm.category_id
        LEFT JOIN FactSales fs ON fs.item_id = dm.item_id
        GROUP BY dm.item_id
        HAVING qty < 5 AND margin_pct > 40
        ORDER BY margin_pct DESC
        LIMIT 5
        """
    ).fetchall()
    for r in rows:
        _add({
            "type":    "promote",
            "icon":    "bi-graph-up-arrow",
            "item":    r["item_name"],
            "category": r["category_name"],
            "message": f"Priority Focus: High profit potential ({r['margin_pct']}% margin) but underperforming in volume. Recommend primary placement in current catalog.",
        })

    # 2. Very low sales AND low margin → consider removing
    rows = c.execute(
        """
        SELECT dm.item_name, dc.category_name,
               COALESCE(SUM(fs.quantity), 0)               AS qty,
               ROUND((dm.price-dm.cost)/dm.price*100, 1)   AS margin_pct
        FROM DimMenuItem dm
        JOIN DimCategory dc ON dc.category_id = dm.category_id
        LEFT JOIN FactSales fs ON fs.item_id = dm.item_id
        GROUP BY dm.item_id
        HAVING qty < 3 AND margin_pct < 30
        ORDER BY qty ASC
        LIMIT 5
        """
    ).fetchall()
    for r in rows:
        _add({
            "type":     "remove",
            "icon":     "bi-trash-fill",
            "item":     r["item_name"],
            "category": r["category_name"],
            "message":  f"Efficiency Risk: Minimal traction and low profitability ({r['margin_pct']}%). Consider archiving to streamline inventory.",
        })

    # 3. Best category per time slot → suggest campaign (one per slot)
    slot_labels = {"morning": "08–12h", "afternoon": "12–18h", "evening": "18–00h"}
    for slot in ("morning", "afternoon", "evening"):
        top = c.execute(
            """
            SELECT dc.category_name, SUM(fs.quantity) AS qty
            FROM FactSales fs
            JOIN DimTime dt ON dt.time_id = fs.time_id AND dt.time_slot = ?
            JOIN DimMenuItem dm ON dm.item_id = fs.item_id
            JOIN DimCategory dc ON dc.category_id = dm.category_id
            GROUP BY dc.category_id
            ORDER BY qty DESC LIMIT 1
            """,
            (slot,),
        ).fetchone()
        if top and top["qty"] > 0:
            _add({
                "type":     "campaign",
                "icon":     "bi-megaphone-fill",
                "item":     top["category_name"],
                "category": slot.capitalize(),
                "message":  (
                    f"Market Opportunity: '{top['category_name']}' demonstrates maximum density during {slot} window. "
                    f"Implement cross-selling strategies to capitalize on this peak."
                ),
            })

    conn.close()
    return recs


# ── AI Strategic Insight Engine ───────────────────────────────────────────────

def get_ai_strategy_context() -> str:
    """
    Generates a structured prompt context for a Local AI (Ollama/LLM).
    Summarizes current performance to get high-level strategic advice.
    """
    kpis = kpi_summary()
    top = top_items(3)
    bottom = bottom_items(3)
    
    context = f"""
Warehouse BI Performance Summary:
- Total Revenue: ${kpis['total_revenue']}
- Avg Order Value: ${kpis['avg_order_value']}
- Total Items Sold: {kpis['total_items_sold']}

Top Performing Products:
{', '.join([f"{i['item_name']} ({i['total_qty']} units)" for i in top])}

Underperforming Products:
{', '.join([f"{i['item_name']} ({i['margin']}% margin)" for i in bottom])}

Goal: Provide 3 professional, actionable strategic insights to improve warehouse efficiency and profitability.
"""
    return context.strip()

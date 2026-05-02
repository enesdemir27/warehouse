from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)
from datetime import datetime
import json

from database import init_db, seed_menu
from etl import load_csv
import analytics as a

app = Flask(__name__)
app.secret_key = "dw-bi-2024"

_initialized = False

@app.before_request
def setup():
    global _initialized
    if not _initialized:
        init_db()
        seed_menu()
        _initialized = True


def _time_slot(hour: int) -> str:
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    return "evening"


# ── Public menu ───────────────────────────────────────────────────────────────

@app.route("/")
def menu():
    now = datetime.now()
    slot = _time_slot(now.hour)
    slot_label = {"morning": "Morning (06–12)", "afternoon": "Afternoon (12–18)", "evening": "Evening (18–23)"}[slot]

    categories = a.category_order_for_slot(slot)
    # Attach items to each category
    for cat in categories:
        cat["menu_items"] = a.menu_items_by_category(cat["category_id"])

    return render_template(
        "menu.html",
        categories=categories,
        slot=slot,
        slot_label=slot_label,
        current_time=now.strftime("%H:%M"),
    )


# ── Admin: dashboard ──────────────────────────────────────────────────────────

@app.route("/admin")
def admin_dashboard():
    kpi      = a.kpi_summary()
    top      = a.top_items(10)
    bottom   = a.bottom_items(10)
    cat_perf = a.category_performance()
    by_hour  = a.sales_by_hour()
    recs     = a.optimization_recommendations()

    # Slot-based category rankings for the comparison table
    slot_rankings = {}
    for slot in ("morning", "afternoon", "evening"):
        slot_rankings[slot] = a.category_order_for_slot(slot)

    return render_template(
        "admin/dashboard.html",
        kpi=kpi,
        top_items=top,
        bottom_items=bottom,
        cat_perf=cat_perf,
        by_hour_json=json.dumps(by_hour),
        cat_perf_json=json.dumps(cat_perf),
        slot_rankings=slot_rankings,
        recommendations=recs,
    )


# ── Admin: upload ─────────────────────────────────────────────────────────────

@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():
    result = None
    if request.method == "POST":
        f = request.files.get("csv_file")
        if not f or not f.filename.endswith(".csv"):
            flash("Please upload a valid .csv file.", "danger")
        else:
            result = load_csv(f.stream)
            flash(
                f"ETL complete: {result['processed']} rows loaded, "
                f"{result['skipped']} skipped.",
                "success" if result["skipped"] == 0 else "warning",
            )
    return render_template("admin/upload.html", result=result)


# ── API endpoints (used by charts) ───────────────────────────────────────────

@app.route("/api/sales-by-hour")
def api_sales_by_hour():
    return jsonify(a.sales_by_hour())


@app.route("/api/category-performance")
def api_category_perf():
    return jsonify(a.category_performance())


@app.route("/api/timeslot-breakdown")
def api_timeslot():
    return jsonify(a.sales_by_timeslot())


@app.route("/api/menu-order")
def api_menu_order():
    hour = datetime.now().hour
    slot = _time_slot(hour)
    return jsonify({"slot": slot, "categories": a.category_order_for_slot(slot)})


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)

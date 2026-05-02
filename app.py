from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)
from datetime import datetime
import json

from db_manager import init_db, seed_menu
from data_loader import load_csv
import bi_engine as a

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
    if 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    return "evening"


# ── Public menu ───────────────────────────────────────────────────────────────

@app.route("/")
def menu():
    # Allow manual hour override for testing/simulation
    override_hour = request.args.get("hour", type=int)
    now = datetime.now()
    now_hour = override_hour if override_hour is not None else now.hour
    
    slot = _time_slot(now_hour)
    slot_label = {
        "morning": "Morning · 08:00–12:00", 
        "afternoon": "Afternoon · 12:00–18:00", 
        "evening": "Evening · 18:00–00:00"
    }[slot]

    categories = a.category_order_for_slot(slot)
    all_items = a.menu_items_with_sales_for_slot(slot)
    
    # Organize items into categories
    for cat in categories:
        cat["menu_items"] = [i for i in all_items if i["category_id"] == cat["category_id"]]

    return render_template(
        "menu.html",
        categories=categories,
        all_items=all_items,
        slot=slot,
        slot_label=slot_label,
        current_time=f"{now_hour:02d}:00",
        current_hour=now_hour,
    )


# ── Admin: dashboard ──────────────────────────────────────────────────────────

@app.route("/admin")
def admin_dashboard():
    kpi      = a.kpi_summary()
    top      = a.top_items(5)
    bottom   = a.bottom_items(5)
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

# Configuration - API Key is loaded from .env for security
import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.route("/admin/ai-insights")
def ai_insights():
    context = a.get_ai_strategy_context()
    import requests

    if GEMINI_API_KEY:
        available_models = []
        list_error_info = ""
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY.strip()}"
            list_res = requests.get(list_url, timeout=5)
            if list_res.status_code == 200:
                available_models = [m['name'].split('/')[-1] for m in list_res.json().get('models', [])]
            else:
                list_error_info = f"List Models Failed: {list_res.status_code} - {list_res.text[:100]}"
        except Exception as e:
            list_error_info = f"List Error: {str(e)}"

        # Using the modern models available in your 2026 API
        models_to_try = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-2.5-flash", "gemini-pro-latest"]
        if available_models:
            models_to_try = [m for m in models_to_try if m in available_models] + [m for m in models_to_try if m not in available_models]

        last_error = ""
        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY.strip()}"
                payload = {"contents": [{"parts": [{"text": context + "\n\nResponse format: Professional, bullet points, strategic tone."}]}]}
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    ai_text = data['candidates'][0]['content']['parts'][0]['text']
                    return jsonify({"success": True, "insight": ai_text})
                else:
                    last_error = f"{model_name} failed ({response.status_code})"
            except Exception as e:
                last_error = str(e)
        
        return jsonify({"success": False, "insight": f"Gemini Error. Available: {available_models}. {list_error_info}. Last: {last_error}"})

    # --- Strategy 2: Local Ollama (Privacy, Offline) ---
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3",
            "prompt": context,
            "stream": False
        }, timeout=5)
        
        if response.status_code == 200:
            ai_text = response.json().get("response", "AI could not generate a response.")
            return jsonify({"success": True, "insight": ai_text})
    except Exception:
        pass

    # --- Fallback: Prompt Digest ---
    return jsonify({
        "success": False, 
        "prompt": context,
        "message": "AI engines (Gemini/Ollama) not active. Please provide a Gemini API Key in app.py or start Ollama."
    })


@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():
    order_result = None
    menu_result = None
    
    if request.method == "POST":
        action = request.form.get("action")
        f = request.files.get("csv_file")
        
        if not f or not f.filename.endswith(".csv"):
            flash("Please upload a valid .csv file.", "danger")
        elif action == "upload_orders":
            order_result = load_csv(f.stream)
            flash(
                f"Orders Loaded: {order_result['processed']} rows.",
                "success" if order_result["skipped"] == 0 else "warning",
            )
        elif action == "upload_menu":
            from db_manager import load_menu_from_stream
            menu_result = load_menu_from_stream(f.stream)
            if menu_result["success"]:
                flash(f"Menu Updated: {menu_result['count']} items loaded.", "success")
            else:
                flash(f"Menu Upload Failed: {menu_result['error']}", "danger")
                
    return render_template("admin/upload.html", order_result=order_result, menu_result=menu_result)


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    print(">>> ADMIN RESET TRIGGERED <<<")
    global _initialized
    import os
    import sqlite3
    from db_manager import DB_PATH, init_db
    
    try:
        # Close any potential connections (just in case)
        # We try to remove the file.
        if os.path.exists(DB_PATH):
            try:
                # Direct SQL wipe as primary (more reliable than file deletion in Windows)
                from db_manager import get_conn
                conn = get_conn()
                c = conn.cursor()
                c.execute("PRAGMA foreign_keys = OFF")
                c.execute("DELETE FROM FactSales")
                c.execute("DELETE FROM DimTime")
                c.execute("DELETE FROM DimMenuItem")
                c.execute("DELETE FROM DimCategory")
                c.execute("DELETE FROM sqlite_sequence")
                conn.commit()
                conn.close()
                print("SQL-level wipe completed.")
            except Exception as sql_e:
                print(f"SQL wipe failed: {sql_e}")
                # Try file removal as fallback
                try:
                    os.remove(DB_PATH)
                    print("Physical file removal completed.")
                except OSError as os_e:
                    print(f"File removal also failed: {os_e}")
        
        # Always run init_db to be sure structure exists
        init_db()
        _initialized = False 
        flash("System Reset Successful! Data cleared.", "success")
    except Exception as e:
        flash(f"Reset process encountered an issue: {str(e)}", "danger")
        
    return redirect(url_for("admin_upload"))


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

import sqlite3
import os
import csv

DB_PATH = os.path.join(os.path.dirname(__file__), "warehouse.db")
MENU_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "menu_items.csv")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # --- Dimension Tables ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS DimCategory (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS DimMenuItem (
            item_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name     TEXT NOT NULL,
            category_id   INTEGER NOT NULL,
            price         REAL NOT NULL,
            cost          REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES DimCategory(category_id),
            UNIQUE (item_name, category_id)
        )
    """)

    # Time dimension: one row per unique (date, hour) combo
    c.execute("""
        CREATE TABLE IF NOT EXISTS DimTime (
            time_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date   TEXT NOT NULL,
            hour         INTEGER NOT NULL,
            day_of_week  TEXT NOT NULL,
            month        INTEGER NOT NULL,
            year         INTEGER NOT NULL,
            time_slot    TEXT NOT NULL,  -- 'morning' | 'afternoon' | 'evening'
            UNIQUE (order_date, hour)
        )
    """)

    # --- Fact Table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS FactSales (
            sale_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     TEXT NOT NULL,
            item_id      INTEGER NOT NULL,
            time_id      INTEGER NOT NULL,
            quantity     INTEGER NOT NULL,
            unit_price   REAL NOT NULL,
            total_price  REAL NOT NULL,
            FOREIGN KEY (item_id)  REFERENCES DimMenuItem(item_id),
            FOREIGN KEY (time_id) REFERENCES DimTime(time_id)
        )
    """)

    conn.commit()
    conn.close()


def load_menu_from_stream(stream):
    """Clear and re-populate the menu dimensions from an uploaded CSV stream."""
    import io
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # 1. Clear existing menu dimensions
        # Note: We don't delete FactSales yet, but if menu changes, sales might reference non-existent items
        # To be safe, we clear everything if the menu is changing.
        c.execute("DELETE FROM DimMenuItem")
        c.execute("DELETE FROM DimCategory")
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('DimMenuItem', 'DimCategory')")
        
        # 2. Load from stream
        if hasattr(stream, 'read'):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8-sig') # Handle potential BOM
            f = io.StringIO(content)
        else:
            f = stream
            
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cat_name = row['category'].strip()
            item_name = row['item_name'].strip()
            price = float(row['price'])
            cost = float(row['cost'])

            c.execute("INSERT OR IGNORE INTO DimCategory (category_name) VALUES (?)", (cat_name,))
            cat_row = c.execute("SELECT category_id FROM DimCategory WHERE category_name = ?", (cat_name,)).fetchone()
            cat_id = cat_row["category_id"]

            c.execute(
                "INSERT OR IGNORE INTO DimMenuItem (item_name, category_id, price, cost) VALUES (?,?,?,?)",
                (item_name, cat_id, price, cost),
            )
            count += 1
            
        conn.commit()
        return {"success": True, "count": count}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def seed_menu():
    """Default seed from local CSV file if exists."""
    if os.path.exists(MENU_CSV_PATH):
        with open(MENU_CSV_PATH, mode='r', encoding='utf-8') as f:
            load_menu_from_stream(f)

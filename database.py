import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "warehouse.db")


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


def seed_menu():
    """Insert default categories and menu items if not already present."""
    conn = get_conn()
    c = conn.cursor()

    categories = [
        "Breakfast", "Lunch", "Dinner",
        "Beverages", "Wine", "Desserts", "Snacks"
    ]

    items = {
        "Breakfast": [
            ("Eggs Benedict", 12.50, 4.00),
            ("Pancakes",      9.00,  2.50),
            ("French Toast",  8.50,  2.00),
            ("Omelette",      10.00, 3.00),
            ("Avocado Toast", 11.00, 3.50),
        ],
        "Lunch": [
            ("Caesar Salad",    11.00, 3.00),
            ("Club Sandwich",   13.00, 4.50),
            ("Grilled Chicken", 16.00, 6.00),
            ("Soup of the Day",  7.00, 1.50),
            ("Pasta Carbonara", 14.00, 4.00),
        ],
        "Dinner": [
            ("Ribeye Steak",  32.00, 12.00),
            ("Grilled Salmon",25.00,  9.00),
            ("Lamb Chops",    28.00, 10.00),
            ("Mushroom Risotto",18.00, 5.00),
            ("Sea Bass",      27.00, 10.00),
        ],
        "Beverages": [
            ("Espresso",     3.50, 0.50),
            ("Cappuccino",   4.50, 1.00),
            ("Fresh Juice",  5.00, 1.50),
            ("Smoothie",     6.00, 2.00),
            ("Soft Drink",   3.00, 0.40),
        ],
        "Wine": [
            ("Red Wine (glass)",    8.00, 2.50),
            ("White Wine (glass)",  8.00, 2.50),
            ("Rosé Wine (glass)",   8.50, 2.50),
            ("Champagne (glass)",  12.00, 4.00),
            ("Prosecco (glass)",    9.00, 3.00),
        ],
        "Desserts": [
            ("Tiramisu",       7.00, 2.00),
            ("Cheesecake",     7.50, 2.50),
            ("Chocolate Cake", 6.50, 2.00),
            ("Crème Brûlée",   8.00, 2.50),
            ("Ice Cream",      5.00, 1.50),
        ],
        "Snacks": [
            ("Nachos",        8.00, 2.00),
            ("Bruschetta",    7.00, 1.50),
            ("Chicken Wings", 11.00, 4.00),
            ("Spring Rolls",  9.00, 2.50),
            ("Onion Rings",   6.50, 1.50),
        ],
    }

    for cat in categories:
        c.execute(
            "INSERT OR IGNORE INTO DimCategory (category_name) VALUES (?)", (cat,)
        )

    for cat_name, menu_items in items.items():
        row = c.execute(
            "SELECT category_id FROM DimCategory WHERE category_name = ?", (cat_name,)
        ).fetchone()
        if not row:
            continue
        cat_id = row["category_id"]
        for name, price, cost in menu_items:
            c.execute(
                """INSERT OR IGNORE INTO DimMenuItem (item_name, category_id, price, cost)
                   VALUES (?,?,?,?)""",
                (name, cat_id, price, cost),
            )

    conn.commit()
    conn.close()

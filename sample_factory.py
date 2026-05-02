"""
Realistic Dynamic Sample Factory:
Generates weighted sales data so 'Top' and 'Bottom' performers are clearly different.
"""

import csv
import random
import os
from datetime import datetime, timedelta
from db_manager import get_conn

def generate_samples(num_orders=150):
    # 1. Get real items from the database
    conn = get_conn()
    c = conn.cursor()
    items = c.execute("SELECT item_name FROM DimMenuItem").fetchall()
    conn.close()

    if not items:
        print("Error: No items found in database. Please upload a menu CSV first.")
        return

    item_list = [r["item_name"] for r in items]
    
    # --- REALISM LOGIC ---
    # Assign random weights to items: some will be 10x more popular than others
    # This creates a clear 'Top 5' and 'Lowest 5'
    weights = {}
    for item in item_list:
        # Most items get weight 1-3, but some lucky items get 15-20
        is_popular = random.random() < 0.2 # 20% of items are 'stars'
        weights[item] = random.randint(15, 25) if is_popular else random.randint(1, 5)

    # 2. Setup simulation parameters
    SLOTS = {
        "morning":   (8, 11),
        "afternoon": (12, 17),
        "evening":   (18, 23),
    }
    
    BASE_DATE = datetime(2024, 3, 1)
    rows = []

    # 3. Generate orders
    for i in range(1, num_orders + 1):
        order_id = f"ORD{i:03d}"
        day_offset = random.randint(0, 29)
        slot_name, (h_min, h_max) = random.choice(list(SLOTS.items()))
        
        hour = random.randint(h_min, h_max)
        minute = random.randint(0, 59)
        dt = BASE_DATE + timedelta(days=day_offset, hours=hour, minutes=minute)

        # Pick random items BASED ON WEIGHTS
        num_items_in_order = random.randint(1, 3)
        # Use random.choices with our realism weights
        chosen_items = random.choices(item_list, weights=[weights[it] for it in item_list], k=num_items_in_order)
        
        for item_name in set(chosen_items): # set() to avoid duplicate items in same order
            qty = random.randint(1, 4)
            rows.append({
                "order_id":       order_id,
                "item_name":      item_name,
                "quantity":       qty,
                "order_datetime": dt.strftime("%Y-%m-%d %H:%M"),
            })

    # 4. Save to CSV
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "sample_orders.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "item_name", "quantity", "order_datetime"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Success: Generated {len(rows)} WEIGHTED transactions.")
    print(f"📈 Realism: Some items now sell significantly more than others.")

if __name__ == "__main__":
    generate_samples()

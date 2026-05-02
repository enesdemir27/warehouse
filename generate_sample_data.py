"""
Run once to produce data/sample_orders.csv (100 rows).
Simulates realistic time-of-day ordering patterns:
  - Morning  (07-11): heavy Breakfast + Beverages
  - Afternoon (12-17): heavy Lunch + Beverages + Wine
  - Evening  (18-22): heavy Dinner + Wine + Desserts
"""

import csv, random, os
from datetime import datetime, timedelta

random.seed(42)

SLOTS = {
    "morning":   (7, 11),
    "afternoon": (12, 17),
    "evening":   (18, 22),
}

# (item_name, slot_weights)  weights = [morning, afternoon, evening]
ITEMS = [
    # Breakfast
    ("Eggs Benedict",    [8, 1, 0]),
    ("Pancakes",         [9, 1, 0]),
    ("French Toast",     [7, 1, 0]),
    ("Omelette",         [6, 2, 1]),
    ("Avocado Toast",    [7, 2, 0]),
    # Lunch
    ("Caesar Salad",     [1, 8, 2]),
    ("Club Sandwich",    [1, 9, 1]),
    ("Grilled Chicken",  [0, 8, 3]),
    ("Soup of the Day",  [1, 7, 2]),
    ("Pasta Carbonara",  [0, 8, 4]),
    # Dinner
    ("Ribeye Steak",     [0, 1, 9]),
    ("Grilled Salmon",   [0, 1, 8]),
    ("Lamb Chops",       [0, 0, 7]),
    ("Mushroom Risotto", [0, 2, 7]),
    ("Sea Bass",         [0, 1, 7]),
    # Beverages
    ("Espresso",         [9, 5, 3]),
    ("Cappuccino",       [8, 4, 2]),
    ("Fresh Juice",      [7, 4, 2]),
    ("Smoothie",         [5, 4, 2]),
    ("Soft Drink",       [3, 6, 5]),
    # Wine
    ("Red Wine (glass)",   [0, 3, 9]),
    ("White Wine (glass)", [0, 4, 8]),
    ("Rosé Wine (glass)",  [0, 3, 7]),
    ("Champagne (glass)",  [0, 2, 6]),
    ("Prosecco (glass)",   [0, 3, 7]),
    # Desserts
    ("Tiramisu",       [1, 2, 8]),
    ("Cheesecake",     [1, 2, 7]),
    ("Chocolate Cake", [1, 2, 7]),
    ("Crème Brûlée",   [0, 1, 8]),
    ("Ice Cream",      [1, 3, 6]),
    # Snacks
    ("Nachos",        [1, 5, 7]),
    ("Bruschetta",    [1, 4, 6]),
    ("Chicken Wings", [1, 4, 8]),
    ("Spring Rolls",  [1, 3, 6]),
    ("Onion Rings",   [1, 4, 5]),
]

BASE_DATE = datetime(2024, 3, 1)
rows = []

for i in range(1, 101):
    order_id = f"ORD{i:03d}"
    day_offset = random.randint(0, 29)
    slot_name, (h_min, h_max) = random.choice(list(SLOTS.items()))
    slot_idx = ["morning", "afternoon", "evening"].index(slot_name)
    hour = random.randint(h_min, h_max)
    minute = random.randint(0, 59)
    dt = BASE_DATE + timedelta(days=day_offset, hours=hour, minutes=minute)

    # pick 1-3 items weighted by slot
    weights = [item[1][slot_idx] for item in ITEMS]
    total_w = sum(weights)
    probs = [w / total_w for w in weights]

    num_items = random.randint(1, 3)
    chosen = random.choices(ITEMS, weights=probs, k=num_items)
    for item_name, _ in chosen:
        qty = random.randint(1, 2)
        rows.append({
            "order_id":       order_id,
            "item_name":      item_name,
            "quantity":       qty,
            "order_datetime": dt.strftime("%Y-%m-%d %H:%M"),
        })

os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
out_path = os.path.join(os.path.dirname(__file__), "data", "sample_orders.csv")
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["order_id", "item_name", "quantity", "order_datetime"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows -> {out_path}")

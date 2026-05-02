import csv
import random
import os
from datetime import datetime, timedelta

SCENARIOS = {
    "sushi_zen": {
        "items": [
            ("Dragon Roll", "Sushi", 18, 6), ("Salmon Nigiri", "Sushi", 12, 4), ("Tuna Sashimi", "Sashimi", 22, 10),
            ("Ebi Tempura", "Hot Dishes", 15, 5), ("Miso Soup", "Hot Dishes", 6, 1), ("Green Tea", "Drinks", 4, 0.5),
            ("Sake Bottle", "Drinks", 35, 12), ("California Roll", "Sushi", 14, 5), ("Edamame", "Hot Dishes", 7, 1.5),
            ("Mochi Ice Cream", "Desserts", 8, 3), ("Yellowtail Roll", "Sushi", 16, 6), ("Spider Roll", "Sushi", 18, 8),
            ("Tuna Nigiri", "Sushi", 13, 4), ("Salmon Sashimi", "Sashimi", 20, 8), ("Gyoza", "Hot Dishes", 9, 3),
            ("Agedashi Tofu", "Hot Dishes", 10, 3), ("Sapporo Beer", "Drinks", 7, 2), ("Ramune Soda", "Drinks", 5, 1.5),
            ("Matcha Cake", "Desserts", 10, 4), ("Tempura Udon", "Hot Dishes", 16, 6), ("Spicy Tuna Roll", "Sushi", 15, 5)
        ]
    },
    "grill_master": {
        "items": [
            ("Ribeye Steak", "Steaks", 45, 20), ("T-Bone Steak", "Steaks", 55, 25), ("Classic Burger", "Burgers", 18, 7),
            ("Bacon Burger", "Burgers", 22, 9), ("Filet Mignon", "Steaks", 50, 22), ("Onion Rings", "Sides", 8, 2),
            ("French Fries", "Sides", 7, 1.5), ("Craft Beer", "Beverages", 10, 3), ("Red Wine Glass", "Beverages", 12, 4),
            ("Grilled Corn", "Sides", 6, 1), ("Sirloin Steak", "Steaks", 38, 16), ("Lamb Chops", "Steaks", 42, 18),
            ("BBQ Ribs", "Steaks", 30, 12), ("Chicken Wings", "Sides", 14, 5), ("Mashed Potatoes", "Sides", 7, 2),
            ("Coleslaw", "Sides", 5, 1), ("Whiskey Sour", "Beverages", 14, 4), ("Lemonade", "Beverages", 5, 1),
            ("New York Cheesecake", "Desserts", 10, 4), ("Chocolate Brownie", "Desserts", 9, 3), ("Wagyu Burger", "Burgers", 35, 15)
        ]
    },
    "pizza_napoli": {
        "items": [
            ("Margherita", "Pizza", 14, 4), ("Pepperoni", "Pizza", 17, 6), ("Quattro Formaggi", "Pizza", 19, 7),
            ("Fettuccine Alfredo", "Pasta", 16, 5), ("Lasagna", "Pasta", 18, 7), ("Caesar Salad", "Salads", 12, 4),
            ("Greek Salad", "Salads", 11, 3.5), ("Tiramisu", "Desserts", 9, 3), ("Espresso", "Drinks", 3.5, 0.5),
            ("Italian Soda", "Drinks", 5, 1), ("Caprese Salad", "Salads", 13, 5), ("Bolognese", "Pasta", 17, 6),
            ("Carbonara", "Pasta", 16, 5), ("Calzone", "Pizza", 18, 7), ("Marinara Pizza", "Pizza", 12, 3),
            ("Focaccia", "Salads", 6, 1), ("Pesto Pasta", "Pasta", 15, 4), ("Prosecco", "Drinks", 12, 4),
            ("Panna Cotta", "Desserts", 8, 3), ("Cannoli", "Desserts", 7, 2.5), ("Burrata", "Salads", 16, 7)
        ]
    }
}

def generate_scenario(name, config):
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    menu_path = os.path.join(data_dir, f"{name}_menu.csv")
    with open(menu_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item_name", "category", "price", "cost"])
        for item in config["items"]:
            writer.writerow(item)
            
    orders_path = os.path.join(data_dir, f"{name}_orders.csv")
    item_names = [it[0] for it in config["items"]]
    random.shuffle(item_names)
    
    top_5 = item_names[:5]
    mid_items = item_names[5:15]
    bottom_5 = item_names[15:]
    
    weights = {}
    for it in top_5:    weights[it] = random.randint(80, 130)
    for it in mid_items:  weights[it] = random.randint(15, 35)
    for it in bottom_5: weights[it] = random.randint(1, 5)
    
    rows = []
    base_date = datetime(2024, 3, 1)
    num_total_orders = 700 
    order_counter = 1
    
    for _ in range(num_total_orders):
        is_dirty_row = random.random() < 0.08 # 8% chance of a dirty row
        order_id = f"ORD{order_counter:04d}"
        dt = base_date + timedelta(days=random.randint(0,29), hours=random.randint(8,23), minutes=random.randint(0,59))
        
        if is_dirty_row:
            dirty_type = random.choice(["bad_date", "bad_qty", "unknown_item", "missing_val"])
            if dirty_type == "bad_date":
                dt_str = "2050-01-01 12:00" # Out of range
            elif dirty_type == "bad_qty":
                qty = random.choice([-5, 500, "NaN"])
            elif dirty_type == "unknown_item":
                item = "Mystery Dish X"
            elif dirty_type == "missing_val":
                item = ""
        
        # Regular or mixed-dirty generation
        num_items_in_order = random.randint(1, 3)
        chosen_items = random.choices(item_names, weights=[weights[it] for it in item_names], k=num_items_in_order)
        
        for item in set(chosen_items):
            qty = random.randint(1, 3)
            dt_str = dt.strftime("%Y-%m-%d %H:%M")
            
            # Add some noise to names/casing (handled by your code)
            final_item = item
            if random.random() < 0.1:
                final_item = f"  {item.upper()}  " 

            # Apply dirty overrides
            if is_dirty_row:
                dirty_type = random.choice(["bad_date", "bad_qty", "unknown_item", "missing_val"])
                if dirty_type == "bad_date": dt_str = "invalid_date_99"
                if dirty_type == "bad_qty": qty = -10
                if dirty_type == "unknown_item": final_item = "Deleted Item #404"
                if dirty_type == "missing_val": final_item = ""

            rows.append({
                "order_id": order_id,
                "item_name": final_item,
                "quantity": qty,
                "order_datetime": dt_str
            })
        order_counter += 1

    with open(orders_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "item_name", "quantity", "order_datetime"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Success: Generated DIRTY Restaurant Scenario: {name}")

if __name__ == "__main__":
    for name, config in SCENARIOS.items():
        generate_scenario(name, config)

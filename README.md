# RestaurantBI — Menu Analysis & Optimization System

**CME 4434 — Data Warehouses and Business Intelligence** course project.

A Flask web application that implements a **star-schema data warehouse** for restaurant order data, performs time-slot-based BI analysis, and dynamically reorders menu categories based on historical sales patterns.

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Smart Menu** | Categories reorder in real time based on the current time slot — breakfast items lead in the morning, wine and dinner dominate in the evening |
| **ETL Pipeline** | Upload a CSV of orders → extract, validate, and load into the warehouse automatically |
| **BI Dashboard** | KPIs, hourly sales chart, category revenue breakdown, top/bottom performers |
| **Optimization Recommendations** | Rule-based suggestions: promote high-margin items, remove low performers, run time-slot campaigns |

---

## Architecture

### Data Warehouse — Star Schema

```
                    ┌─────────────────┐
                    │   DimCategory   │
                    │─────────────────│
                    │ category_id  PK │
                    │ category_name   │
                    └────────┬────────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌──────────────────┐
│   DimTime    │    │   FactSales     │    │   DimMenuItem    │
│──────────────│    │─────────────────│    │──────────────────│
│ time_id   PK │◄───│ sale_id      PK │───►│ item_id       PK │
│ order_date   │    │ order_id        │    │ item_name        │
│ hour         │    │ item_id      FK │    │ category_id   FK │
│ day_of_week  │    │ time_id      FK │    │ price            │
│ month        │    │ quantity        │    │ cost             │
│ year         │    │ unit_price      │    └──────────────────┘
│ time_slot    │    │ total_price     │
└──────────────┘    └─────────────────┘
```

**Time slots:** `morning` (06–12h) · `afternoon` (12–18h) · `evening` (18–23h)

### ETL Flow

```
CSV Upload → Parse & Validate → Lookup Dimensions → Insert FactSales → BI Queries
```

### Project Structure

```
warehouse/
├── app.py                     # Flask routes
├── database.py                # Schema init + menu seed (star schema)
├── etl.py                     # ETL: CSV → data warehouse
├── analytics.py               # All BI queries (KPIs, rankings, recommendations)
├── generate_sample_data.py    # Generates 100 realistic sample orders
├── requirements.txt
├── data/
│   └── sample_orders.csv      # 100 orders, 204 line items
├── static/
│   ├── css/style.css
│   └── sample_orders.csv      # Downloadable from the upload page
└── templates/
    ├── base.html
    ├── menu.html               # Public menu (smart category ordering)
    └── admin/
        ├── dashboard.html      # Analytics dashboard
        └── upload.html         # ETL upload panel
```

---

## Getting Started

### Requirements

- Python **3.10+**
- pip

### Install & Run

```bash
# 1. Clone the repository
git clone https://github.com/enesdemir27/warehouse.git
cd warehouse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate sample order data (optional — repo already includes it)
python generate_sample_data.py

# 4. Start the application
python app.py
```

The app runs at **http://127.0.0.1:5000**

> **First run:** The database (`warehouse.db`) is created and seeded automatically on startup. No separate setup step needed.

### Load Sample Data

1. Open **http://127.0.0.1:5000/admin/upload**
2. Upload `data/sample_orders.csv`
3. The ETL pipeline loads 204 order line items into the warehouse

---

## Pages

| URL | Description |
|-----|-------------|
| `/` | Public menu — smart category ordering by current time slot |
| `/admin` | Analytics dashboard — KPIs, charts, rankings, recommendations |
| `/admin/upload` | Upload orders CSV — runs the ETL pipeline |

---

## CSV Format

Upload files must have these four columns:

```
order_id,item_name,quantity,order_datetime
ORD001,Pancakes,2,2024-03-01 08:15
ORD001,Espresso,1,2024-03-01 08:15
ORD002,Caesar Salad,1,2024-03-01 13:20
ORD003,Red Wine (glass),2,2024-03-01 19:45
```

- `order_datetime` format: `YYYY-MM-DD HH:MM`
- One row per item; multiple rows share the same `order_id`
- `item_name` must match a menu item exactly (case-insensitive)

---

## Team Roles (CME 4434)

| Role | Responsibility |
|------|---------------|
| **Person 1** | Project analysis, problem definition, requirements, system flow |
| **Person 2** | Data warehouse design, star schema, ETL process (`database.py`, `etl.py`) |
| **Person 3** | BI analysis, KPIs, optimization logic (`analytics.py`) |
| **Person 4** | Application, dashboard, GitHub integration (`app.py`, templates) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 · Flask |
| Database | SQLite (star schema) |
| ETL | Pure Python (csv module) |
| Frontend | Bootstrap 5 · Chart.js · Bootstrap Icons |
| Data | Pandas (sample generation only) |

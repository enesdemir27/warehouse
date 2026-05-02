# CoreBI — Universal Warehouse & Business Intelligence Platform

A high-performance, sector-neutral **Data Warehouse and Business Intelligence (BI)** dashboard designed for real-time inventory and sales analysis. 

Built for modern businesses, this platform implements a **Star Schema architecture**, robust **ETL pipelines**, and dynamic **Time-Slot analysis** to optimize category positioning and surface actionable insights.

---

## 💎 Core Features

| Feature | Description |
|---------|-------------|
| **Smart Catalog** | Categories dynamically reorder based on the current time slot using historical sales density. |
| **ETL Engine** | Automated ingestion pipeline: Upload CSV → Validate → Normalize → Load into Warehouse. |
| **Enterprise Dashboard** | Real-time KPIs, hourly performance metrics, and revenue breakdown. |
| **Optimization Logic** | Intelligent recommendations for promoting high-margin items and pruning low-performers. |
| **Industry Agnostic** | Fully configurable for Retail, Logistics, F&B, or any inventory-based business. |

---

## 🏗️ Architecture

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

**Operating Window:** 08:00 – 00:00 (Customizable)

### ETL & Data Flow
1. **Extract:** Standardized CSV ingestion.
2. **Transform:** Data normalization, time-slot mapping, and error handling.
3. **Load:** Direct injection into the SQLite star schema.

---

## 📂 Project Structure

```
warehouse/
├── app.py                # Main Application & API Routes
├── bi_engine.py          # Business Intelligence Engine & Optimization Logic
├── db_manager.py         # Schema Management & Database Operations
├── data_loader.py        # ETL Pipeline: CSV Ingestion & Validation
├── sample_factory.py     # High-fidelity Synthetic Data Generator
├── requirements.txt      # Platform Dependencies
├── data/                 # Operational Data Storage (CSV)
├── static/               # UI Assets (CSS, JS)
└── templates/            # Dynamic Web Interfaces
```

---

## 🚀 Deployment

### Requirements
- Python **3.10+**
- Virtual Environment (Recommended)

### Quick Start

```bash
# 1. Initialize environment
pip install -r requirements.txt

# 2. Generate initial datasets (Optional)
python sample_factory.py

# 3. Launch the platform
python app.py
```

The platform is accessible at **http://127.0.0.1:5000**

---

## 📊 Operational Insights

The system analyzes data across three primary dimensions:
- **Morning (08:00–12:00):** Early-day operational focus.
- **Afternoon (12:00–18:00):** Peak mid-day traffic.
- **Evening (18:00–00:00):** High-margin evening operations.

---

## 🛠️ Technology Stack

- **Backend:** Flask (Python 3)
- **Database:** SQLite (Star Schema Optimized)
- **Visualization:** Chart.js & Bootstrap 5
- **Icons:** Bootstrap Icons (Industry Neutral)

"""
ETL module: parse uploaded CSV orders and load into the data warehouse.

Expected CSV columns:
  order_id, item_name, quantity, order_datetime
  e.g.: ORD001, Pancakes, 2, 2024-03-15 08:30
"""

import csv
import io
from datetime import datetime
from db_manager import get_conn


def _time_slot(hour: int) -> str:
    if 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def _day_name(dt: datetime) -> str:
    return dt.strftime("%A")


def _get_or_create_time(c, dt: datetime) -> int:
    date_str = dt.strftime("%Y-%m-%d")
    row = c.execute(
        "SELECT time_id FROM DimTime WHERE order_date=? AND hour=?",
        (date_str, dt.hour),
    ).fetchone()
    if row:
        return row["time_id"]
    c.execute(
        """INSERT INTO DimTime (order_date, hour, day_of_week, month, year, time_slot)
           VALUES (?,?,?,?,?,?)""",
        (
            date_str,
            dt.hour,
            _day_name(dt),
            dt.month,
            dt.year,
            _time_slot(dt.hour),
        ),
    )
    return c.lastrowid


def load_csv(file_stream) -> dict:
    """
    Accepts a file-like object (CSV). Returns a summary dict with
    rows_processed, rows_skipped, errors.
    """
    conn = get_conn()
    c = conn.cursor()

    if isinstance(file_stream, (bytes, bytearray)):
        raw = file_stream
    else:
        raw = file_stream.read()
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    # Normalise column names (strip whitespace, lower)
    processed = skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in row.items()}

        try:
            order_id   = row["order_id"]
            item_name  = row["item_name"]
            quantity   = int(row["quantity"])
            dt_raw     = row["order_datetime"]
        except KeyError as e:
            errors.append(f"Row {i}: missing column {e}")
            skipped += 1
            continue
        except ValueError as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
            continue

        # Parse datetime (accept "YYYY-MM-DD HH:MM" or "YYYY-MM-DD HH:MM:SS")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(dt_raw, fmt)
                break
            except ValueError:
                dt = None
        if dt is None:
            errors.append(f"Row {i}: bad datetime '{dt_raw}'")
            skipped += 1
            continue
        
        # Date range validation: skip very old or far-future dates
        if not (2020 <= dt.year <= 2030):
            errors.append(f"Row {i}: date out of range ({dt.year}) — skipped")
            skipped += 1
            continue

        # Debug: check what items exist if we fail
        # (This helps us see if the menu was actually synced)
        
        # Look up item (Case-insensitive + Stripped)
        item = c.execute(
            "SELECT item_id, price FROM DimMenuItem WHERE lower(trim(item_name))=lower(trim(?))",
            (item_name,),
        ).fetchone()
        if not item:
            errors.append(f"Row {i}: unknown item '{item_name}' — skipped")
            skipped += 1
            continue

        # Outlier detection: skip unrealistic quantities
        if quantity <= 0 or quantity > 100:
            errors.append(f"Row {i}: unrealistic quantity ({quantity}) — skipped")
            skipped += 1
            continue

        time_id = _get_or_create_time(c, dt)
        c.execute(
            """INSERT INTO FactSales
               (order_id, item_id, time_id, quantity, unit_price, total_price)
               VALUES (?,?,?,?,?,?)""",
            (
                order_id,
                item["item_id"],
                time_id,
                quantity,
                item["price"],
                item["price"] * quantity,
            ),
        )
        processed += 1

    conn.commit()
    conn.close()
    return {"processed": processed, "skipped": skipped, "errors": errors}

"""
Transformer
-----------
Takes a raw row (from a reader) and the source's config, and produces
a single, clean, Silver-shaped row -- typed, deduped-ready, and fully
traceable back to its source. This is the ONLY place business meaning
gets attached to raw data; readers stay dumb on purpose.
"""

import hashlib
from datetime import datetime, timezone


def transform_row(raw_row: dict, config: dict, source_file: str, source_format: str) -> dict:
    """
    Transform one raw row into a Silver-shaped record.
    """
    # Job 3: drop artifact keys (e.g. the '' key from trailing-comma CSVs).
    # Deliberately done here, not in the reader -- readers stay dumb.
    clean_row = {k: v for k, v in raw_row.items() if k}

    # Pull real values using the config's column mapping, not hardcoded
    # column names -- this is what makes the function source-agnostic.
    period_raw = clean_row[config["column_mapping"]["period_column"]]
    value_raw = clean_row[config["column_mapping"]["value_column"]]

    # Job 2: normalise the period into a real date, first-of-month.
    period_date = datetime.strptime(period_raw + "-01", "%Y-%m-%d").date()

    # Job 1: force the value into a proper number, regardless of whether
    # it arrived as a string (CSV) or an int (XLSX).
    indicator_value = float(value_raw)

    # Job 7: validate before handing off.
    if indicator_value < 0:
        raise ValueError(
            f"Negative indicator_value ({indicator_value}) for "
            f"{config['indicator_code']} in period {period_raw} "
            f"from {source_file} -- refusing to load."
        )

    # Job 5: build the deterministic surrogate key. Same inputs always
    # produce the same key -- this is what makes the loader's
    # MERGE/upsert idempotent, the actual fix for the duplicate-row
    # problem measured in the legacy scripts.
    key_fields = [
        config["source_publisher"],
        config["indicator_code"],
        config["geography"],
        str(period_date),
    ]
    indicator_id = hashlib.sha256("|".join(key_fields).encode()).hexdigest()

    # Job 4 + 6: attach identity fields (from config) and lineage fields.
    return {
        "indicator_id": indicator_id,
        "source_publisher": config["source_publisher"],
        "indicator_code": config["indicator_code"],
        "indicator_name": config["indicator_name"],
        "geography": config["geography"],
        "period_date": period_date,
        "period_grain": config["period_grain"],
        "indicator_value": indicator_value,
        "unit": config["unit"],
        "dim_supplier": None,  # only populated for Ofgem's SNAPSHOT grain, later
        "source_file": source_file,
        "source_format": source_format,
        "extracted_at": datetime.now(timezone.utc),
    }
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


def transform_row(raw_row: dict, config: dict, source_file: str, source_format: str) -> list[dict]:
    """
    Transform one raw row into one OR MORE Silver-shaped records.

    FSA-style configs (flat column_mapping, one indicator) produce
    exactly one record. Insolvency Service-style configs (a list of
    column mappings, many indicators per row) produce one record per
    mapping entry that has a real value for this particular row.
    """
    clean_row = {k: v for k, v in raw_row.items() if k}

    mapping = config["column_mapping"]
    if isinstance(mapping, dict):
        entries = [{
            "source_column": mapping["period_column"],
            "indicator_code": config["indicator_code"],
            "indicator_name": config["indicator_name"],
            "geography": config["geography"],
            "unit": config["unit"],
        }]
        value_columns = [mapping["value_column"]]
        period_column = mapping["period_column"]
    else:
        entries = mapping
        value_columns = [e["source_column"] for e in entries]
        period_column = "period"

    period_raw = clean_row[period_column]
    period_date = datetime.strptime(period_raw + "-01", "%Y-%m-%d").date()

    results = []
    for entry, source_col in zip(entries, value_columns):
        raw_value = clean_row.get(source_col)
        if raw_value in (None, "", "[x]", "[z]"):
            continue

        indicator_value = float(raw_value)
        if indicator_value < 0:
            raise ValueError(f"Negative value for {entry['indicator_code']} in {period_raw} from {source_file}")

        # Build a lookup of every value that COULD be part of a dedup key,
        # then genuinely read config["dedup_key"] to decide which of these
        # actually get hashed, in the order it specifies. This is what
        # makes dedup_key a real, load-bearing config field.
        available_values = {
            "source_publisher": config["source_publisher"],
            "indicator_code": entry["indicator_code"],
            "geography": entry["geography"],
            "period_date": str(period_date),
        }
        key_fields = [str(available_values[field]) for field in config["dedup_key"]]
        indicator_id = hashlib.sha256("|".join(key_fields).encode()).hexdigest()

        results.append({
            "indicator_id": indicator_id,
            "source_publisher": config["source_publisher"],
            "indicator_code": entry["indicator_code"],
            "indicator_name": entry["indicator_name"],
            "geography": entry["geography"],
            "period_date": period_date,
            "period_grain": config["period_grain"],
            "indicator_value": indicator_value,
            "unit": entry["unit"],
            "dim_supplier": None,
            "source_file": source_file,
            "source_format": source_format,
            "extracted_at": datetime.now(timezone.utc),
        })

    return results
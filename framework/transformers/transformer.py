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



def parse_ons_period(period_raw) -> tuple:
    """
    ONS's M1 sheet mixes four period formats in one column:
      - Financial year, string:  'Apr 1997 to Mar 1998'
      - Quarter, abbreviated:    'Jul to Sep 2022'
      - Quarter, full month:     'April to Jun 2023' (ONS's own
        inconsistent spelling -- confirmed real, not our error)
      - Bare calendar year, int: 1997

    Returns a (period_date, period_grain) tuple, so the caller knows
    both the normalised date AND which grain this particular row
    actually represents -- necessary because, unlike every other
    source, grain varies row-to-row here, not per-config.
    """
    MONTH_TO_NUMBER = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "April": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    if isinstance(period_raw, int):
        return datetime(period_raw, 1, 1).date(), "YEAR"

    if " to " not in period_raw:
        raise ValueError(f"Unrecognised ONS period format: {period_raw!r}")

    start_part, end_part = period_raw.split(" to ")
    start_part = start_part.strip()
    end_month_name, end_year_str = end_part.strip().rsplit(" ", 1)
    end_year = int(end_year_str)

    # A financial year's start side has a year attached ("Apr 1997");
    # a quarter's start side is just the month ("Jul"). That presence
    # of a year is the real signal, not the month name alone.
    start_words = start_part.split(" ")
    if len(start_words) == 2:
        # Financial year: "Apr 1997 to Mar 1998" -> starts 1 Apr 1997
        start_month_name, start_year_str = start_words
        return datetime(int(start_year_str), MONTH_TO_NUMBER[start_month_name], 1).date(), "FINANCIAL_YEAR"

    # Otherwise, a calendar quarter: "Jul to Sep 2022" -> starts 1 Jul 2022
    start_month_number = MONTH_TO_NUMBER[start_part]
    return datetime(end_year, start_month_number, 1).date(), "QUARTER"



def parse_period(period_raw: str, period_grain: str):
    """
    Normalise a raw period string into a real date, first-of-period,
    according to the grain the config declares. SNAPSHOT indicators
    never call this at all -- they have no period, handled separately
    in transform_row.
    """
    if period_grain == "MONTH":
        return datetime.strptime(period_raw + "-01", "%Y-%m-%d").date()

    if period_grain == "QUARTER":
        quarter_str, year_str = period_raw.split(" ")
        quarter_number = int(quarter_str.replace("Q", ""))
        first_month_of_quarter = {1: 1, 2: 4, 3: 7, 4: 10}[quarter_number]
        return datetime(int(year_str), first_month_of_quarter, 1).date()

    raise ValueError(f"Unsupported period_grain: {period_grain}")


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

    row_period_grain = config["period_grain"]

    if config["period_grain"] == "SNAPSHOT":
        period_date = None
        dim_supplier_value = clean_row[period_column]
    elif config["period_grain"] == "MIXED":
        period_raw = clean_row[period_column]
        period_date, row_period_grain = parse_ons_period(period_raw)
        dim_supplier_value = None
    else:
        period_raw = clean_row[period_column]
        period_date = parse_period(period_raw, config["period_grain"])
        dim_supplier_value = None

    results = []
    for entry, source_col in zip(entries, value_columns):
        raw_value = clean_row.get(source_col)
        if raw_value in (None, "", "[x]", "[z]"):
            continue

        indicator_value = float(raw_value)
        if indicator_value < 0:
            raise ValueError(f"Negative value for {entry['indicator_code']} from {source_file}")

        available_values = {
            "source_publisher": config["source_publisher"],
            "indicator_code": entry["indicator_code"],
            "geography": entry["geography"],
            "period_date": str(period_date),
            "dim_supplier": str(dim_supplier_value),
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
            "period_grain": row_period_grain,
            "indicator_value": indicator_value,
            "unit": entry["unit"],
            "dim_supplier": dim_supplier_value,
            "source_file": source_file,
            "source_format": source_format,
            "extracted_at": datetime.now(timezone.utc),
        })

    return results
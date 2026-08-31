"""
Generates one config file per remaining ONS M1-family sheet (M2-M7),
deriving every column mapping from real headers rather than hand-
typing them -- these sheets have up to 17 columns each, several with
embedded newlines and [note N] references, exactly the kind of thing
that's caused real transcription errors tonight. Also handles a real,
confirmed inconsistency: M5 and M6 use 'Time Period' (capital P)
where every other sheet uses 'Time period' -- reading the real header
rather than hardcoding it sidesteps this entirely.
"""

import re
from framework.readers.xlsx_reader import read_xlsx

LATEST_FILE = "bronze/ons/rftm17tables (5).xlsx"
EARLIEST_FILE = "bronze/ons/rftm17tables.xlsx"

SHEETS = ["M2", "M3", "M4", "M5", "M6", "M7"]


def derive_indicator_code(column_name: str) -> str:
    clean = re.sub(r"\[note \d+\]", "", column_name)
    clean = re.sub(r"[^\w\s]", "", clean)
    clean = re.sub(r"\s+", "_", clean.strip())
    return clean.upper()[:60]


def derive_unit(column_name: str) -> str:
    lower = column_name.lower()
    if "percentage points" in lower:
        return "percentage points"
    if "£ million" in lower:
        return "£ million"
    return "unknown"


def generate_sheet_config(sheet_name: str) -> dict:
    sample_row = read_xlsx(LATEST_FILE, sheet=sheet_name, header_row=5, skip_rows_after_header=1)[0]
    headers = [h for h in sample_row.keys() if h is not None]
    period_column = headers[0]
    value_columns = headers[1:]

    column_mapping = []
    for col in value_columns:
        column_mapping.append({
            "source_column": col,
            "indicator_code": derive_indicator_code(col),
            "indicator_name": re.sub(r"\s*\[note \d+\]", "", col).replace("\n", " ").strip(),
            "geography": "United Kingdom",
            "unit": derive_unit(col),
        })

    return {
        "source_publisher": "ONS",
        "geography": "United Kingdom",
        "period_grain": "MIXED",
        "period_column": period_column,
        "allow_negative_values": True,
        "files": [
            {"path": EARLIEST_FILE, "format": "xlsx", "sheet": sheet_name, "header_row": 5, "skip_rows_after_header": 1},
            {"path": LATEST_FILE, "format": "xlsx", "sheet": sheet_name, "header_row": 5, "skip_rows_after_header": 1},
        ],
        "column_mapping": column_mapping,
        "dedup_key": ["source_publisher", "indicator_code", "geography", "period_date"],
    }


if __name__ == "__main__":
    import yaml

    for sheet_name in SHEETS:
        config = generate_sheet_config(sheet_name)
        output_path = f"framework/config/sources/ons_{sheet_name.lower()}.yaml"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(
                f"# ONS Government Deficit and Debt ({sheet_name})\n"
                f"# Generated from real reader output -- column count and "
                f"exact\n# text varies too much per sheet to hand-type "
                f"safely (M5 alone has\n# 17 columns). Real inconsistency "
                f"confirmed: this sheet's period\n# column is named "
                f"'{config['period_column']}'.\n\n"
            )
            yaml.dump(config, f, sort_keys=False, allow_unicode=True)
        print(f"{sheet_name}: {len(config['column_mapping'])} indicators -> {output_path}")
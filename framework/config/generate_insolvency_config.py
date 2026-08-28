"""
Generates the column_mapping section of the Insolvency Service config
directly from the publisher's own Metadata CSV, rather than hand-typing
33 entries. This is run once, manually, when the config needs building
or refreshing -- it is not part of the pipeline itself.
"""

import csv

METADATA_FILE = "bronze/insolvency_service/Metadata_for_Long-Run_Series_in_CSV_Format_-_Individual_Insolvency_Statistics_October_2024.csv"

UNIT_HINTS = {
    "rate_per_10000": "rate per 10,000 adults",
}


def infer_unit(variable_name: str) -> str:
    if "rate_per_10000" in variable_name:
        return "rate per 10,000 adults"
    return "count"


def generate_mapping():
    with open(METADATA_FILE, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # The real header row starts at line 11 (index 10), confirmed
    # during profiling: "Variable,Description,Geography,..."
    data_rows = rows[10:]

    mapping = []
    for row in data_rows:
        if not row or not row[0] or row[0] in ("Period", "Year", "Month"):
            continue  # skip blank rows and the non-indicator date columns
        variable, description = row[0], row[1]
        mapping.append({
            "source_column": variable,
            "indicator_code": variable.upper(),
            "indicator_name": description,
            "geography": "England & Wales",
            "unit": infer_unit(variable),
        })
    return mapping


if __name__ == "__main__":
    import yaml
    mapping = generate_mapping()
    print(f"Generated {len(mapping)} column mappings.")
    print(yaml.dump(mapping, sort_keys=False))
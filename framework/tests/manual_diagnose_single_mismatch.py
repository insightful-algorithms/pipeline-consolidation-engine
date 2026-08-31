"""
Manual utility: diagnoses exactly why one specific config value
doesn't match the real header it's supposed to represent. Finds the
first differing character and its Unicode code point -- useful for
catching invisible differences a normal print would hide (different
dash types, non-breaking spaces, curly vs straight apostrophes).

Usage:
    python -m framework.tests.manual_diagnose_single_mismatch <config_name> <sheet> <search_text>

Example:
    python -m framework.tests.manual_diagnose_single_mismatch ons_m4 M4 non-debt
"""

import sys
import yaml
from framework.readers.xlsx_reader import read_xlsx


def diagnose(config_name: str, sheet: str, search_text: str):
    config_path = f"framework/config/sources/{config_name}.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config_value = next(
        (entry["source_column"] for entry in config["column_mapping"] if search_text in entry["source_column"]),
        None,
    )
    if config_value is None:
        print(f"No column in config containing {search_text!r}")
        return

    file_entry = config["files"][0]
    sample_row = read_xlsx(
        file_entry["path"],
        sheet=sheet,
        header_row=file_entry.get("header_row", 1),
        skip_rows_after_header=file_entry.get("skip_rows_after_header", 0),
    )[0]
    real_header = next((h for h in sample_row.keys() if h and search_text in h), None)
    if real_header is None:
        print(f"No real header containing {search_text!r}")
        return

    print("Config value:", repr(config_value))
    print("Real header: ", repr(real_header))
    print("Equal?", config_value == real_header)

    if config_value != real_header:
        for i, (a, b) in enumerate(zip(config_value, real_header)):
            if a != b:
                print(f"First difference at position {i}: config has {a!r} ({ord(a)}), real has {b!r} ({ord(b)})")
                break
        else:
            print(f"One string is a prefix of the other. Config length: {len(config_value)}, real length: {len(real_header)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m framework.tests.manual_diagnose_single_mismatch <config_name> <sheet> <search_text>")
        sys.exit(1)
    diagnose(sys.argv[1], sys.argv[2], sys.argv[3])
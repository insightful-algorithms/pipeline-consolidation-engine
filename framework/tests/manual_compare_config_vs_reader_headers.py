"""
Manual utility: compares the source_column values stored in a config
file's column_mapping against the ACTUAL headers read.py produces
fresh from the real file. If a config was written by dumping a
sample row to YAML and reading it back, subtle differences (YAML's
newline folding rules, trailing whitespace) can mean the two no
longer match exactly -- causing every value lookup to silently return
None with no error at all.
"""

import sys
import yaml
from framework.readers.xlsx_reader import read_xlsx


def compare(config_name: str):
    path = f"framework/config/sources/{config_name}.yaml"
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    file_entry = config["files"][0]
    sample_row = read_xlsx(
        file_entry["path"],
        sheet=file_entry["sheet"],
        header_row=file_entry.get("header_row", 1),
        skip_rows_after_header=file_entry.get("skip_rows_after_header", 0),
    )[0]
    real_headers = set(sample_row.keys())

    config_columns = [entry["source_column"] for entry in config["column_mapping"]]

    print(f"=== {config_name} ===")
    for col in config_columns:
        match = "OK" if col in real_headers else "MISMATCH"
        print(f"  [{match}] {col!r}")

    if config.get("period_column") not in real_headers:
        print(f"  [MISMATCH] period_column: {config.get('period_column')!r}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m framework.tests.manual_compare_config_vs_reader_headers <config_name>")
        sys.exit(1)
    compare(sys.argv[1])
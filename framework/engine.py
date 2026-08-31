"""
Engine
------
Orchestrates one source end-to-end. Supports two config shapes:

1. "files"-shaped configs (FSA, Insolvency Service): one shared list
   of files, all feeding the same indicator(s) via column_mapping.
2. "indicators"-shaped configs (Ofgem): a list of standalone
   indicators, each with its own single file and its own column
   mapping -- effectively many small, self-contained configs bundled
   into one YAML file, because each Ofgem file genuinely has a
   different shape from every other Ofgem file.

Adding a fifth source means writing a config in whichever shape
actually fits its real structure -- this function decides which
loading strategy to use based on which top-level key is present.
"""

import yaml
from framework.readers.csv_reader import read_csv
from framework.readers.xlsx_reader import read_xlsx
from framework.transformers.transformer import transform_row
from framework.loaders.sqlite_loader import load_rows

READERS = {
    "csv": lambda file_entry: read_csv(file_entry["path"]),
    "xlsx": lambda file_entry: read_xlsx(
        file_entry["path"],
        sheet=file_entry["sheet"],
        header_row=file_entry.get("header_row", 1),
        skip_rows_after_header=file_entry.get("skip_rows_after_header", 0),
    ),
}


def run_source(config_path: str) -> dict:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if "indicators" in config:
        return _run_indicators_shaped_source(config)
    else:
        return _run_files_shaped_source(config)


def _run_files_shaped_source(config: dict) -> dict:
    """FSA and Insolvency Service shape: one shared file list."""
    all_rows = []
    for file_entry in config["files"]:
        reader_fn = READERS[file_entry["format"]]
        raw_rows = reader_fn(file_entry)
        for raw_row in raw_rows:
            all_rows.extend(
                transform_row(
                    raw_row, config,
                    source_file=file_entry["path"],
                    source_format=file_entry["format"],
                )
            )
    return load_rows(all_rows)


def _run_indicators_shaped_source(config: dict) -> dict:
    """Ofgem shape: many standalone indicators, each with its own file."""
    all_rows = []
    for indicator in config["indicators"]:
        # SNAPSHOT indicators have no period, so period_date is always
        # None for every row -- geography and indicator_code alone
        # can't tell one supplier's row apart from another's. dim_supplier
        # replaces period_date in the dedup key for exactly this reason.
        dedup_key = (
            ["source_publisher", "indicator_code", "geography", "dim_supplier"]
            if indicator["period_grain"] == "SNAPSHOT"
            else ["source_publisher", "indicator_code", "geography", "period_date"]
        )

        single_indicator_config = {
            "source_publisher": config["source_publisher"],
            "indicator_code": indicator["indicator_code"],
            "indicator_name": indicator["indicator_name"],
            "geography": config["geography"],
            "unit": indicator["unit"],
            "period_grain": indicator["period_grain"],
            "column_mapping": {
                "period_column": indicator["period_column"],
                "value_column": indicator["value_column"],
            },
            "dedup_key": dedup_key,
        }

        raw_rows = read_csv(indicator["file_path"])
        for raw_row in raw_rows:
            all_rows.extend(
                transform_row(
                    raw_row, single_indicator_config,
                    source_file=indicator["file_path"],
                    source_format="csv",
                )
            )
    return load_rows(all_rows)


if __name__ == "__main__":
    result = run_source("framework/config/sources/fsa.yaml")
    print(result)
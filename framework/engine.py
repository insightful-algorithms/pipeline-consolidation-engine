"""
Engine
------
Orchestrates one source end-to-end: reads its config, picks the right
reader per file based on config-declared format, transforms every row,
and loads the result. This is what makes the pipeline config-driven --
adding a fifth source means writing a config file, never touching this
function.
"""

import yaml
from framework.readers.csv_reader import read_csv
from framework.readers.xlsx_reader import read_xlsx
from framework.transformers.transformer import transform_row
from framework.loaders.sqlite_loader import load_rows

READERS = {
    "csv": lambda file_entry: read_csv(file_entry["path"]),
    "xlsx": lambda file_entry: read_xlsx(file_entry["path"], sheet=file_entry["sheet"]),
}


def run_source(config_path: str) -> dict:
    """
    Run the full pipeline for one source, given its config file path.
    Returns the loader's post-load validation summary.
    """
    with open(config_path) as f:
        config = yaml.safe_load(f)

    all_rows = []
    for file_entry in config["files"]:
        reader_fn = READERS[file_entry["format"]]
        raw_rows = reader_fn(file_entry)
        for raw_row in raw_rows:
            all_rows.append(
                transform_row(
                    raw_row,
                    config,
                    source_file=file_entry["path"],
                    source_format=file_entry["format"],
                )
            )

    return load_rows(all_rows)


if __name__ == "__main__":
    result = run_source("framework/config/sources/fsa.yaml")
    print(result)
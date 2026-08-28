"""
Manual check: proves revision detection works against real data.

Loads Insolvency Service's October 2024 release first, then the
July 2026 release -- which we confirmed during profiling genuinely
revises historical figures, including the earliest data point in the
whole series (2000-01). Watch `revisions_logged_this_run` on the
second load: given the confirmed finding, this should be a large
number, not zero.

Not a formal automated test yet (no pass/fail assertions) -- kept here
as a real, re-runnable script rather than retyped into the shell each
time.
"""

import yaml
from framework.readers.csv_reader import read_csv
from framework.transformers.transformer import transform_row
from framework.loaders.sqlite_loader import load_rows


def run():
    with open("framework/config/sources/insolvency_service.yaml") as f:
        config = yaml.safe_load(f)

    path_old = "bronze/insolvency_service/Long-Run_Series_in_CSV_Format_-_Individual_Insolvency_Statistics_October_2024.csv"
    rows_old = read_csv(path_old)
    transformed_old = []
    for r in rows_old:
        transformed_old.extend(transform_row(r, config, source_file=path_old, source_format="csv"))
    print("Loading October 2024:", load_rows(transformed_old))

    path_new = "bronze/insolvency_service/Long-Run_Series_in_CSV_Format_-_Individual_Insolvency_Statistics_July_2026.csv"
    rows_new = read_csv(path_new)
    transformed_new = []
    for r in rows_new:
        transformed_new.extend(transform_row(r, config, source_file=path_new, source_format="csv"))
    print("Loading July 2026:", load_rows(transformed_new))


if __name__ == "__main__":
    run()
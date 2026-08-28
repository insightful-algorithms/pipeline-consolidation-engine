"""
CSV Reader
----------
Reads a CSV file and returns its rows as plain Python dictionaries.
Knows nothing about indicators, columns that matter, or business
meaning -- that interpretation belongs to the transformer, not here.
"""

import csv


def read_csv(path: str) -> list[dict]:
    """
    Read a CSV file and return its rows as a list of dictionaries,
    one dict per row, keyed by the file's own header names.
    """
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows
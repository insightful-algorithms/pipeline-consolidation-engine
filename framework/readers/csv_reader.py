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
    Read a CSV file and return its rows as a list of dictionaries.

    Headers that are blank or whitespace-only (a real, confirmed
    artifact in several Ofgem exports) are given a stable positional
    name (col_1, col_2, ...) rather than being silently dropped --
    this preserves real data that just happens to arrive with no
    column name, without making any judgement about what it means.
    """
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        headers = [
            h.strip() if h.strip() else f"col_{i+1}"
            for i, h in enumerate(raw_headers)
        ]
        for row in reader:
            rows.append(dict(zip(headers, row)))
    return rows
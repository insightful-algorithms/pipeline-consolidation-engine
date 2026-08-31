"""
CSV Reader
----------
Reads a CSV file and returns its rows as plain Python dictionaries.
Knows nothing about indicators, columns that matter, or business
meaning -- that interpretation belongs to the transformer, not here.
"""

import csv
import re


def read_csv(path: str) -> list[dict]:
    """
    Read a CSV file and return its rows as a list of dictionaries.

    Two real, confirmed export artifacts are handled here, at the
    structural level, since neither is a business decision:

    1. Headers that are blank or whitespace-only (seen in several
       Ofgem files) are given a stable positional name (col_1, col_2,
       ...) rather than being silently dropped.
    2. Headers containing leftover HTML tags (e.g. "<div>Quarter /
       Year</div>", also seen in a real Ofgem file) have those tags
       stripped before the blank-check runs -- otherwise a header
       that's genuinely meaningful once cleaned would be wrongly
       treated as data instead of being recognised as the real column
       name it is.
    """
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        headers = [
            re.sub(r"<[^>]+>", "", h).strip() if h.strip() else f"col_{i+1}"
            for i, h in enumerate(raw_headers)
        ]
        for row in reader:
            rows.append(dict(zip(headers, row)))
    return rows
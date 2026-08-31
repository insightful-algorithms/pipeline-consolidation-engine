"""
XLSX Reader
-----------
Reads an Excel (.xlsx) file and returns rows from a named sheet as
plain Python dictionaries. Like the CSV reader, this module knows
nothing about which columns matter -- that's the transformer's job.
"""

import openpyxl


def read_xlsx(path: str, sheet: str, header_row: int = 1, skip_rows_after_header: int = 0) -> list[dict]:
    """
    Read a single sheet from an XLSX file and return its rows as a
    list of dictionaries, keyed by that sheet's own header row.

    header_row and skip_rows_after_header default to FSA's simple
    shape (header on row 1, data starts immediately after). ONS's M1
    sheet needs header_row=5 and skip_rows_after_header=1, since its
    real header sits five rows down and is followed by a metadata row
    ("Dataset identifier code") that must be skipped, not read as data.
    """
    workbook = openpyxl.load_workbook(path, data_only=True)
    worksheet = workbook[sheet]

    all_rows = list(worksheet.iter_rows(values_only=True))
    headers = all_rows[header_row - 1]
    data_rows = all_rows[header_row + skip_rows_after_header:]

    rows = []
    for row in data_rows:
        if row[0] is None:
            continue
        rows.append(dict(zip(headers, row)))

    return rows
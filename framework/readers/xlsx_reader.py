"""
XLSX Reader
-----------
Reads an Excel (.xlsx) file and returns rows from a named sheet as
plain Python dictionaries. Like the CSV reader, this module knows
nothing about which columns matter -- that's the transformer's job.
"""

import openpyxl


def read_xlsx(path: str, sheet: str) -> list[dict]:
    """
    Read a single sheet from an XLSX file and return its rows as a
    list of dictionaries, keyed by that sheet's own header row.
    """
    workbook = openpyxl.load_workbook(path, data_only=True)
    worksheet = workbook[sheet]

    rows_iterator = worksheet.iter_rows(values_only=True)
    headers = next(rows_iterator)

    rows = []
    for row in rows_iterator:
        if row[0] is None:
            continue
        rows.append(dict(zip(headers, row)))

    return rows
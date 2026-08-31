"""
Manual utility: reads one raw cell directly from an XLSX file using
openpyxl only, with none of our own reader/transformer code involved.
Used to check whether a suspicious character (e.g. the "double-
encoded" A-with-circumflex-pound symbol seen in ONS's M2-M7 sheets)
is already present in the source file itself, or introduced somewhere
in our own pipeline.
"""

import sys
import openpyxl


def compare(path: str, sheet_names: list[str], row: int, col_index: int):
    wb = openpyxl.load_workbook(path, data_only=True)
    for sheet_name in sheet_names:
        ws = wb[sheet_name]
        row_values = list(ws.iter_rows(min_row=row, max_row=row, values_only=True))[0]
        print(f"{sheet_name} header cell {col_index + 1}: {row_values[col_index]!r}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python -m framework.tests.manual_compare_raw_cell_encoding <path> <row> <col_index> <sheet1> [sheet2] ...")
        sys.exit(1)

    path = sys.argv[1]
    row = int(sys.argv[2])
    col_index = int(sys.argv[3])
    sheet_names = sys.argv[4:]
    compare(path, sheet_names, row, col_index)
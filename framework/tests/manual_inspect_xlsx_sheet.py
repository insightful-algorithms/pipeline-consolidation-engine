"""
Manual utility: dump the first several rows of one or more sheets in
an XLSX file, so real header/structure can be confirmed before
designing a config for it -- the same discipline used for every
source tonight, now reusable instead of retyped each time.

Usage:
    python -m framework.tests.manual_inspect_xlsx_sheet <path> <sheet1> [sheet2] ...

Example:
    python -m framework.tests.manual_inspect_xlsx_sheet "bronze/ons/rftm17tables (5).xlsx" M2 M3 M4 M5 M6 M7
"""

import sys
import openpyxl


def inspect(path: str, sheet_names: list[str], max_rows: int = 8):
    wb = openpyxl.load_workbook(path, data_only=True)
    for sheet_name in sheet_names:
        ws = wb[sheet_name]
        print(f"=== {sheet_name} ===")
        for row in ws.iter_rows(min_row=1, max_row=max_rows, values_only=True):
            vals = [v for v in row if v is not None]
            if vals:
                print(vals)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m framework.tests.manual_inspect_xlsx_sheet <path> <sheet1> [sheet2] ...")
        sys.exit(1)

    path = sys.argv[1]
    sheet_names = sys.argv[2:]
    inspect(path, sheet_names)
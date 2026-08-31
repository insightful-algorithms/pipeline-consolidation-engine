"""
Generates the Insolvency-Service-style column_mapping for ONS's M1
sheet directly from real reader output -- avoids hand-typing column
names that contain embedded newlines and note references, which is
exactly the kind of thing easy to get subtly wrong by hand.
"""

from framework.readers.xlsx_reader import read_xlsx

sample_row = read_xlsx(
    "bronze/ons/rftm17tables (5).xlsx",
    sheet="M1",
    header_row=5,
    skip_rows_after_header=1,
)[0]

INDICATOR_CODES = {
    "General government net borrowing \n(£ million)": ("NET_BORROWING", "General government net borrowing", "£ million"),
    "General government gross consolidated debt at nominal value (£ million)": ("GROSS_DEBT", "General government gross consolidated debt at nominal value", "£ million"),
    "Gross domestic product (GDP) at current market prices (£ million) [note 2]": ("GDP_CURRENT_PRICES", "Gross domestic product (GDP) at current market prices", "£ million"),
    "Net borrowing as a percentage of GDP (percentage points) \n[note 2]": ("NET_BORROWING_PCT_GDP", "Net borrowing as a percentage of GDP", "percentage points"),
    "Gross consolidated debt as a percentage of GDP (percentage points) [note 2]": ("GROSS_DEBT_PCT_GDP", "Gross consolidated debt as a percentage of GDP", "percentage points"),
}

column_mapping = []
for real_column_name, (code, name, unit) in INDICATOR_CODES.items():
    assert real_column_name in sample_row, f"Column not found in real data: {real_column_name!r}"
    column_mapping.append({
        "source_column": real_column_name,
        "indicator_code": code,
        "indicator_name": name,
        "geography": "United Kingdom",
        "unit": unit,
    })

if __name__ == "__main__":
    import yaml

    config = {
        "source_publisher": "ONS",
        "geography": "United Kingdom",
        "period_grain": "MIXED",
        "files": [
            {"path": "bronze/ons/rftm17tables.xlsx", "format": "xlsx", "sheet": "M1",
             "header_row": 5, "skip_rows_after_header": 1},
            {"path": "bronze/ons/rftm17tables (5).xlsx", "format": "xlsx", "sheet": "M1",
             "header_row": 5, "skip_rows_after_header": 1},
        ],
        "column_mapping": column_mapping,
        "dedup_key": ["source_publisher", "indicator_code", "geography", "period_date"],
    }

    output_path = "framework/config/sources/ons.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            "# ONS Government Deficit and Debt (M1 sheet only for now)\n"
            "# Scope: M1 -- 5 headline indicators, mixed period grain\n"
            "# (financial year / quarter / bare calendar year, all in one\n"
            "# column). M2-M7 and the discontinued M8R revisions table are\n"
            "# a deliberate follow-up, not covered here.\n"
            "# The assert above confirms every real column name matches\n"
            "# what's actually in the file before writing anything.\n\n"
        )
        yaml.dump(config, f, sort_keys=False, allow_unicode=True)

    print(f"Written to {output_path}")
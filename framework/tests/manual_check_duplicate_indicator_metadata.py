"""
Manual utility: finds indicator_code values that share the same code
but have inconsistent metadata (name, unit, or grain) across rows --
the exact condition that breaks a naive DISTINCT-based dim table
build, since DISTINCT checks the whole row, not just the key column.
"""

import sys
import sqlite3

DB_PATH = "warehouse/dev.db"


def check():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT indicator_code, COUNT(DISTINCT indicator_name || '|' || unit || '|' || period_grain) as variants
        FROM stg_debt_indicators
        GROUP BY indicator_code
        HAVING variants > 1
    """).fetchall()
    conn.close()

    print(f"{len(rows)} indicator_code values with inconsistent metadata:")
    for code, variant_count in rows:
        print(f"  {code}: {variant_count} variants")


def inspect_one(indicator_code: str):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT DISTINCT indicator_name, unit, period_grain, source_publisher
        FROM stg_debt_indicators
        WHERE indicator_code = ?
    """, (indicator_code,)).fetchall()
    conn.close()

    print(f"Variants for {indicator_code}:")
    for r in rows:
        print(f"  {r}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_one(sys.argv[1])
    else:
        check()
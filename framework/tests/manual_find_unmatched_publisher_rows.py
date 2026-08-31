"""
Manual utility: finds which stg_debt_indicators rows have no matching
row in dim_source_publisher when joined the same way build_gold.py
joins them -- used to find the exact cause of a NOT NULL constraint
failure on fact_debt_indicators.source_publisher_key, rather than
guessing at a fix.
"""

import sqlite3

DB_PATH = "warehouse/dev.db"


def find_unmatched():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT s.source_publisher, s.period_date, COUNT(*)
        FROM stg_debt_indicators s
        LEFT JOIN dim_source_publisher p
            ON s.source_publisher = p.source_publisher
            AND (s.period_date IS NULL OR (s.period_date >= p.valid_from AND s.period_date <= p.valid_to))
        WHERE p.source_publisher_key IS NULL
        GROUP BY s.source_publisher, s.period_date
        LIMIT 20
    """).fetchall()
    conn.close()

    print(f"{len(rows)} distinct (publisher, period_date) combos with no dim_source_publisher match:")
    for source_publisher, period_date, count in rows:
        print(f"  publisher={source_publisher!r}  period_date={period_date!r}  affected_rows={count}")


if __name__ == "__main__":
    find_unmatched()
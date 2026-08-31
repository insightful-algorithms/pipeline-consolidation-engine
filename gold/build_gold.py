"""
Builds the Gold-layer star schema from Silver's stg_debt_indicators,
using plain SQL against SQLite.

Note: this was originally attempted with PySpark and Delta Lake, the
intended production approach. PySpark's local inter-process networking
failed consistently on this Windows/WSL2 environment even after the
standard fixes (HADOOP_HOME/winutils, firewall exception, explicit
driver bind address) -- a genuine, documented environment limitation,
not a flaw in the Gold-layer design itself. The star schema below is
identical in structure to what the Spark version would have produced;
only the execution engine differs.

dim_source_publisher uses SCD Type 2, justified by a real, confirmed
finding: ONS renamed its reference table from RFTM18 to RFTM17 between
March and June 2025, discontinuing the M8R official revisions table
at that exact transition.

Commits after each table, not just once at the end -- a real lesson
from this build: an uncommitted multi-step script means any failure
partway through silently discards everything, even the steps that
already succeeded. Confirmed directly: a crash on fact_debt_indicators
wiped out three already-built dimension tables that had never been
committed.
"""

import sqlite3

DB_PATH = "warehouse/dev.db"


def build_gold():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── dim_date ─────────────────────────────────────────────────────────
    cur.execute("DROP TABLE IF EXISTS dim_date")
    cur.execute("""
        CREATE TABLE dim_date (
            date_key TEXT PRIMARY KEY,
            full_date TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            quarter INTEGER NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO dim_date (date_key, full_date, year, month, quarter)
        SELECT DISTINCT
            period_date,
            period_date,
            CAST(substr(period_date, 1, 4) AS INTEGER),
            CAST(substr(period_date, 6, 2) AS INTEGER),
            ((CAST(substr(period_date, 6, 2) AS INTEGER) - 1) / 3) + 1
        FROM stg_debt_indicators
        WHERE period_date IS NOT NULL
    """)
    print(f"dim_date rows: {cur.execute('SELECT COUNT(*) FROM dim_date').fetchone()[0]}")
    conn.commit()

    # ── dim_source_publisher (SCD Type 2) ───────────────────────────────
    cur.execute("DROP TABLE IF EXISTS dim_source_publisher")
    cur.execute("""
        CREATE TABLE dim_source_publisher (
            source_publisher_key TEXT PRIMARY KEY,
            source_publisher TEXT NOT NULL,
            reference_code TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT NOT NULL,
            is_current INTEGER NOT NULL
        )
    """)
    publisher_history = [
        ("FSA_1900-01-01", "FSA", "FSA_DEBTOR_DAYS", "1900-01-01", "9999-12-31", 1),
        ("INSOLVENCY_SERVICE_1900-01-01", "INSOLVENCY_SERVICE", "LONG_RUN_SERIES", "1900-01-01", "9999-12-31", 1),
        ("OFGEM_1900-01-01", "OFGEM", "DEBT_ARREARS_INDICATORS", "1900-01-01", "9999-12-31", 1),
        ("ONS_1900-01-01", "ONS", "RFTM18", "1900-01-01", "2025-05-31", 0),
        ("ONS_2025-06-01", "ONS", "RFTM17", "2025-06-01", "9999-12-31", 1),
    ]
    cur.executemany(
        "INSERT INTO dim_source_publisher VALUES (?, ?, ?, ?, ?, ?)",
        publisher_history,
    )
    print(f"dim_source_publisher rows: {cur.execute('SELECT COUNT(*) FROM dim_source_publisher').fetchone()[0]} "
          f"(5 = 4 publishers, ONS split into 2 real SCD Type 2 versions)")
    conn.commit()

    # ── dim_indicator_type ───────────────────────────────────────────────
    # period_grain deliberately excluded -- it varies per FACT row for
    # MIXED-grain sources like ONS (the same NET_BORROWING indicator
    # legitimately appears as FINANCIAL_YEAR, QUARTER, and YEAR rows),
    # so it belongs on fact_debt_indicators via the Silver row, not as
    # part of what defines a distinct indicator TYPE. Confirmed by
    # inspecting real data before making this fix, not assumed.
    cur.execute("DROP TABLE IF EXISTS dim_indicator_type")
    cur.execute("""
        CREATE TABLE dim_indicator_type (
            indicator_type_key TEXT PRIMARY KEY,
            indicator_code TEXT NOT NULL,
            indicator_name TEXT NOT NULL,
            unit TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO dim_indicator_type (indicator_type_key, indicator_code, indicator_name, unit)
        SELECT DISTINCT indicator_code, indicator_code, indicator_name, unit
        FROM stg_debt_indicators
    """)
    print(f"dim_indicator_type rows: {cur.execute('SELECT COUNT(*) FROM dim_indicator_type').fetchone()[0]}")
    conn.commit()

    # ── fact_debt_indicators ──────────────────────────────────────────────
    cur.execute("DROP TABLE IF EXISTS fact_debt_indicators")
    cur.execute("""
        CREATE TABLE fact_debt_indicators (
            fact_id TEXT PRIMARY KEY,
            indicator_id TEXT NOT NULL,
            source_publisher_key TEXT NOT NULL,
            indicator_type_key TEXT NOT NULL,
            geography TEXT NOT NULL,
            date_key TEXT,
            indicator_value REAL NOT NULL,
            dim_supplier TEXT,
            source_file TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO fact_debt_indicators
        SELECT
            lower(hex(randomblob(16))),
            s.indicator_id,
            p.source_publisher_key,
            s.indicator_code,
            s.geography,
            s.period_date,
            s.indicator_value,
            s.dim_supplier,
            s.source_file
        FROM stg_debt_indicators s
        LEFT JOIN dim_source_publisher p
            ON s.source_publisher = p.source_publisher
            -- s.period_date = 'None' handles a real quirk: SNAPSHOT-grain
            -- rows (Ofgem supplier comparisons) have Python None for
            -- period_date, but sqlite_loader.py's str(row["period_date"])
            -- converts that to the literal text 'None' before storage --
            -- not a true SQL NULL, so IS NULL alone doesn't catch it.
            AND (s.period_date IS NULL OR s.period_date = 'None' OR (s.period_date >= p.valid_from AND s.period_date <= p.valid_to))
    """)
    print(f"fact_debt_indicators rows: {cur.execute('SELECT COUNT(*) FROM fact_debt_indicators').fetchone()[0]}")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_debt_indicators(date_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_publisher_indicator ON fact_debt_indicators(source_publisher_key, indicator_type_key)")

    conn.commit()
    conn.close()
    print("\nGold build complete.")


if __name__ == "__main__":
    build_gold()
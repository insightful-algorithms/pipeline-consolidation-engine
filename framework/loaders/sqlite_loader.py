"""
SQLite Loader
-------------
Loads transformed Silver-shaped rows into a SQLite database using an
idempotent MERGE/upsert pattern keyed on indicator_id. Running this
loader twice against the same data must produce zero duplicate rows --
that's the direct fix for the duplication measured in every legacy
script (16 duplicates for FSA alone).

Every value is inserted using parameterized queries (the ? placeholders
below) -- never string concatenation -- so no external data can ever
be interpreted as a SQL command.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "warehouse" / "dev.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stg_debt_indicators (
    indicator_id      TEXT PRIMARY KEY,
    source_publisher  TEXT NOT NULL,
    indicator_code    TEXT NOT NULL,
    indicator_name    TEXT NOT NULL,
    geography         TEXT NOT NULL,
    period_date       TEXT NOT NULL,
    period_grain      TEXT NOT NULL,
    indicator_value   REAL NOT NULL CHECK (indicator_value >= 0),
    unit              TEXT NOT NULL,
    dim_supplier      TEXT,
    source_file       TEXT NOT NULL,
    source_format     TEXT NOT NULL,
    extracted_at      TEXT NOT NULL
)
"""


CREATE_REVISIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS indicator_revisions (
    revision_id         TEXT PRIMARY KEY,
    indicator_id         TEXT NOT NULL,
    source_publisher      TEXT NOT NULL,
    indicator_code         TEXT NOT NULL,
    geography               TEXT NOT NULL,
    period_date              TEXT NOT NULL,
    previous_value            REAL NOT NULL,
    new_value                  REAL NOT NULL,
    previous_source_file        TEXT NOT NULL,
    new_source_file               TEXT NOT NULL,
    detection_method               TEXT NOT NULL,
    detected_at                     TEXT NOT NULL
)
"""



# ON CONFLICT ... DO UPDATE is SQLite's MERGE/upsert syntax. It means:
# "try to insert this row; if a row with this indicator_id already
# exists, update it instead of failing or creating a duplicate."
UPSERT_SQL = """
INSERT INTO stg_debt_indicators (
    indicator_id, source_publisher, indicator_code, indicator_name,
    geography, period_date, period_grain, indicator_value, unit,
    dim_supplier, source_file, source_format, extracted_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(indicator_id) DO UPDATE SET
    indicator_value = excluded.indicator_value,
    source_file     = excluded.source_file,
    source_format   = excluded.source_format,
    extracted_at    = excluded.extracted_at
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_REVISIONS_TABLE_SQL)
    return conn



import uuid  # add this import at the top of the file, alongside sqlite3 and Path

REVISION_INSERT_SQL = """
INSERT INTO indicator_revisions (
    revision_id, indicator_id, source_publisher, indicator_code, geography,
    period_date, previous_value, new_value, previous_source_file,
    new_source_file, detection_method, detected_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

def load_rows(rows: list[dict]) -> dict:
    conn = get_connection()
    revisions_logged = 0

    for row in rows:
        # Check-then-act: look up what's already there BEFORE writing.
        existing = conn.execute(
            "SELECT indicator_value, source_file FROM stg_debt_indicators WHERE indicator_id = ?",
            (row["indicator_id"],)
        ).fetchone()

        if existing is not None:
            existing_value, existing_source_file = existing
            if existing_value != row["indicator_value"]:
                # A real revision: same indicator, same period, different value.
                conn.execute(REVISION_INSERT_SQL, (
                    str(uuid.uuid4()),
                    row["indicator_id"],
                    row["source_publisher"],
                    row["indicator_code"],
                    row["geography"],
                    str(row["period_date"]),
                    existing_value,
                    row["indicator_value"],
                    existing_source_file,
                    row["source_file"],
                    "SILENT_DIFF",
                    str(row["extracted_at"]),
                ))
                revisions_logged += 1

        conn.execute(UPSERT_SQL, (
            row["indicator_id"], row["source_publisher"], row["indicator_code"],
            row["indicator_name"], row["geography"], str(row["period_date"]),
            row["period_grain"], row["indicator_value"], row["unit"],
            row["dim_supplier"], row["source_file"], row["source_format"],
            str(row["extracted_at"]),
        ))

    conn.commit()

    total_rows = conn.execute("SELECT COUNT(*) FROM stg_debt_indicators").fetchone()[0]
    distinct_keys = conn.execute("SELECT COUNT(DISTINCT indicator_id) FROM stg_debt_indicators").fetchone()[0]
    conn.close()

    return {
        "rows_processed_this_run": len(rows),
        "total_rows_in_table": total_rows,
        "distinct_indicator_ids": distinct_keys,
        "duplicates_found": total_rows - distinct_keys,
        "revisions_logged_this_run": revisions_logged,
    }









# def load_rows(rows: list[dict]) -> dict:
#     """
#     Load a list of Silver-shaped rows and return post-load validation
#     counts -- row counts and duplicate checks, per standard practice.
#     """
#     conn = get_connection()

#     for row in rows:
#         # Every value passed as a separate parameter (the tuple below),
#         # never glued into the SQL string itself. This is exactly the
#         # parameterized-query pattern -- it's what stops any value,
#         # however it's formed, from ever being read as a SQL command.
#         conn.execute(UPSERT_SQL, (
#             row["indicator_id"],
#             row["source_publisher"],
#             row["indicator_code"],
#             row["indicator_name"],
#             row["geography"],
#             str(row["period_date"]),
#             row["period_grain"],
#             row["indicator_value"],
#             row["unit"],
#             row["dim_supplier"],
#             row["source_file"],
#             row["source_format"],
#             str(row["extracted_at"]),
#         ))

#     conn.commit()

#     # Post-load validation: row count and duplicate check.
#     total_rows = conn.execute("SELECT COUNT(*) FROM stg_debt_indicators").fetchone()[0]
#     distinct_keys = conn.execute("SELECT COUNT(DISTINCT indicator_id) FROM stg_debt_indicators").fetchone()[0]

#     conn.close()

#     return {
#         "rows_processed_this_run": len(rows),
#         "total_rows_in_table": total_rows,
#         "distinct_indicator_ids": distinct_keys,
#         "duplicates_found": total_rows - distinct_keys,
#     }
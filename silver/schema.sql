-- ============================================================================
-- Silver Layer Schema — stg_debt_indicators and indicator_revisions
-- ============================================================================
-- This file documents the schema that framework/loaders/sqlite_loader.py
-- creates at runtime (CREATE_TABLE_SQL, CREATE_REVISIONS_TABLE_SQL). Kept
-- here as the canonical reference, since docs/SILVER_SCHEMA_DESIGN.md
-- explains the reasoning behind every column and needs a real schema
-- file to point to.
-- ============================================================================

CREATE TABLE IF NOT EXISTS stg_debt_indicators (
    indicator_id      TEXT PRIMARY KEY,
    source_publisher  TEXT NOT NULL,
    indicator_code    TEXT NOT NULL,
    indicator_name    TEXT NOT NULL,
    geography         TEXT NOT NULL,
    period_date       TEXT NOT NULL,
    period_grain      TEXT NOT NULL,
    indicator_value   REAL NOT NULL,
    unit              TEXT NOT NULL,
    dim_supplier      TEXT,
    source_file       TEXT NOT NULL,
    source_format     TEXT NOT NULL,
    extracted_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS indicator_revisions (
    revision_id            TEXT PRIMARY KEY,
    indicator_id            TEXT NOT NULL,
    source_publisher         TEXT NOT NULL,
    indicator_code            TEXT NOT NULL,
    geography                  TEXT NOT NULL,
    period_date                 TEXT NOT NULL,
    previous_value                REAL NOT NULL,
    new_value                       REAL NOT NULL,
    previous_source_file             TEXT NOT NULL,
    new_source_file                    TEXT NOT NULL,
    detection_method                     TEXT NOT NULL,
    detected_at                            TEXT NOT NULL
);
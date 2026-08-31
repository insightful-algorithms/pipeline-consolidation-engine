"""
Tests the full FSA pipeline end-to-end against real data, asserting
the two specific things we reasoned through:

1. The exact expected row count (32 distinct months) -- catches bugs
   that silently DROP real data, which a duplicates-only check would miss.
2. Zero duplicates -- catches the exact problem measured in the legacy
   script (48 rows for 32 months, 16 real duplicates).

Checking only one of these can hide a failure the other would catch --
that's why both assertions exist together, not as alternatives.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_fsa_pipeline_produces_correct_row_count_and_no_duplicates():
    # Start from a clean database, so this test's result depends only
    # on this run -- not on whatever happened to be loaded before it.
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/fsa.yaml")

    assert result["rows_for_this_source"] == 32, (
        f"Expected 32 distinct FSA months, got {result['rows_for_this_source']}"
    )
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
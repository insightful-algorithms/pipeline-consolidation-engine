"""
Tests the Insolvency Service Debt Relief Orders by Authorising Body
pipeline (Table_7a) end to end against real data. Confirms the
unpivot logic (transform_wide_row) is genuinely correct, not just
error-free -- a wide-to-long transform has more ways to silently lose
or duplicate data than a normal row-per-period source.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_insolvency_service_authorising_body_pipeline_produces_correct_row_count_and_no_duplicates():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/insolvency_service_authorising_body.yaml")

    assert result["rows_for_this_source"] == 750, (
        f"Expected 750 authorising body indicator rows, "
        f"got {result['rows_for_this_source']}"
    )
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
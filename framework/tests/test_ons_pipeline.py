"""
Tests the full ONS pipeline end-to-end against real data.

Same row-count and duplicate checks as every other source. Unlike
Ofgem, ONS DOES have confirmed real revisions -- 420 were detected
across the M1 sheet during profiling, including a headline net
borrowing figure that changed between the June 2025 and June 2026
releases. Asserting revisions_logged_this_run > 0, the same pattern
used for Insolvency Service, proves detection genuinely fires for
this source too, not just the one it was originally built against.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_ons_pipeline_produces_correct_row_count_and_no_duplicates():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/ons_m1.yaml")

    assert result["rows_for_this_source"] == 585, (
        f"Expected 585 ONS indicator rows, got {result['rows_for_this_source']}"
    )
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
    assert result["revisions_logged_this_run"] > 0, (
        "Expected at least one revision to be detected -- ONS is a "
        "confirmed-revisions source (e.g. net borrowing for Apr 1997 "
        "to Mar 1998 changed between real releases). Zero revisions "
        "here would mean detection silently stopped firing for this "
        "source."
    )
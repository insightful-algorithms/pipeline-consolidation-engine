"""
Tests the full Ofgem pipeline end-to-end against real data.

Same row-count and duplicate checks as every other source. The
revisions_logged_this_run == 0 assertion is deliberate, not an
oversight: Ofgem has no revision concept in this dataset -- only one
download exists per indicator, so there is nothing to compare
against. Asserting this explicitly, rather than leaving it untested,
means a future non-zero result is caught and investigated -- whether
that turns out to be a genuine change in Ofgem's publishing pattern
(multiple dated snapshots) or a bug producing false revisions.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_ofgem_pipeline_produces_correct_row_count_and_no_duplicates():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/ofgem.yaml")

    assert result["rows_for_this_source"] == 1005, (
        f"Expected 1005 Ofgem indicator rows, got {result['rows_for_this_source']}"
    )
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
    assert result["revisions_logged_this_run"] == 0, (
        "Expected zero revisions -- Ofgem provides only one snapshot "
        "per indicator, so there is nothing to compare against. A "
        "non-zero result here means either Ofgem's publishing pattern "
        "has genuinely changed, or revision detection is misfiring."
    )
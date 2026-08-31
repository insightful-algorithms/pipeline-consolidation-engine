"""
Tests the full Insolvency Service pipeline end-to-end against real
data. Same discipline as test_fsa_pipeline.py: exact expected row
count (catches silent data loss) plus zero duplicates (catches the
naive-append problem measured in the legacy script).

One addition specific to this source: unlike FSA, Insolvency Service
has CONFIRMED real revisions (the 2000-01 figure that changed between
releases). A single clean run through all three files still triggers
revision detection, because the files are processed in order within
one call and later files' values genuinely differ from earlier ones
for overlapping periods. Asserting revisions_logged_this_run > 0
proves the detection logic actually fires for this source, rather
than only being tested in isolation via manual_revision_check.py.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_insolvency_service_pipeline_produces_correct_row_count_and_no_duplicates():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/insolvency_service.yaml")

    assert result["rows_for_this_source"] == 7671, (
    f"Expected 7671 distinct Insolvency Service indicator rows, "
    f"got {result['rows_for_this_source']}"
)
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
    assert result["revisions_logged_this_run"] > 0, (
        "Expected at least one revision to be detected -- Insolvency "
        "Service is a confirmed-revisions source (e.g. the 2000-01 "
        "total individuals figure changed between real releases). "
        "Zero revisions here would mean the detection logic silently "
        "stopped firing for this source."
    )
"""
Tests the Insolvency Service Northern Ireland pipeline (Table_9) end
to end against real data. Same discipline as every other source test:
exact row count, zero duplicates, and a revision check.

Table_9 shares source_publisher with the main England & Wales config,
so this test clears the database and loads ONLY this config, the same
way every other test isolates its own source before asserting a count.

revisions_logged_this_run > 0 is asserted because 28 real revisions
were confirmed when this source first loaded successfully -- though
unlike the England & Wales 2000-01 figure, no single NI revision has
been independently verified by hand yet. That's a known, honest gap:
the detection mechanism itself is already proven correct against two
other sources, but this specific number hasn't been hand-checked.
"""

import os
from framework.engine import run_source

DB_PATH = "warehouse/dev.db"


def test_insolvency_service_ni_pipeline_produces_correct_row_count_and_no_duplicates():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    result = run_source("framework/config/sources/insolvency_service_ni.yaml")

    assert result["rows_for_this_source"] == 364, (
        f"Expected 364 Northern Ireland indicator rows, "
        f"got {result['rows_for_this_source']}"
    )
    assert result["duplicates_found"] == 0, (
        f"Expected zero duplicates, found {result['duplicates_found']}"
    )
    assert result["revisions_logged_this_run"] > 0, (
        "Expected revisions to be detected -- 28 were confirmed on "
        "first successful load of this source. Zero here would mean "
        "detection silently stopped firing."
    )
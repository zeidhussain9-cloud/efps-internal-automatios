import re

from src import pipeline


def test_new_row_onboarded_on_is_date_only():
    row = pipeline.initial_row("EF-2611-TEST", "raw")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["onboarded_on"])


def test_supplied_onboarded_on_is_kept():
    assert pipeline.initial_row("EF-2611-TEST", "raw", onboarded_on="2026-11-21")["onboarded_on"] == "2026-11-21"

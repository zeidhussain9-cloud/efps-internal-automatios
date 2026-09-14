from __future__ import annotations

from . import batch, pipeline


def test_batch_only_selects_processed_raw_text_rows():
    ready = pipeline.initial_row("EF-2609-1001")
    ready["raw_message_text"] = "2 BHK Rent 50000"
    waiting_no_text = pipeline.initial_row("EF-2609-1002")
    waiting_no_text["raw_message_text"] = ""
    locked = pipeline.initial_row("EF-2609-1003")
    locked["raw_message_text"] = "2 BHK Rent 50000"
    locked["intake_status"] = "Processed"

    assert batch.eligible(ready)
    assert not batch.eligible(waiting_no_text)
    assert not batch.eligible(locked)


def test_batch_does_not_select_row_without_listing_id():
    row = pipeline.initial_row("")
    row["raw_message_text"] = "2 BHK Rent 50000"
    assert not batch.eligible(row)

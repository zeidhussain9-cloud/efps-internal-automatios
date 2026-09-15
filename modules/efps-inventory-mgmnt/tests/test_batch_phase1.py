from __future__ import annotations

from src import batch
from src.pipeline import initial_row
from shared.google_sheets import schema


class FakeBatchClient:
    def __init__(self, row: dict):
        self.values = [schema.mapping_to_row(row)]
        self.reads = []
        self.writes = []

    def read_range(self, spreadsheet_id, worksheet_name, range_name):
        self.reads.append(range_name)
        return self.values

    def write_ranges(self, spreadsheet_id, worksheet_name, updates):
        self.writes.append(updates)


def test_batch_phase1_uses_one_read_and_one_batch_write():
    row = initial_row("EF-TEST-BATCH", raw_text="2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur")
    client = FakeBatchClient(row)
    result = batch.run(client, start_row=2, end_row=2)
    assert result["considered"] == 1
    assert result["processed"] == 1
    assert result["write_failed"] is False
    assert client.reads == ["A2:AV2"]
    assert len(client.writes) == 1
    assert len(client.writes[0]) == 3
    assert result["rows"][0]["fields"]["populated"]


def test_batch_eligibility_skips_already_processed_rows_for_resumability():
    row = initial_row("EF-TEST-BATCH-RESUME", raw_text="2 BHK\nRent: 40000")
    row["intake_status"] = "Processed"
    client = FakeBatchClient(row)
    result = batch.run(client, start_row=2, end_row=2)
    assert result["considered"] == 0
    assert result["skipped"] == 1
    assert client.writes == []

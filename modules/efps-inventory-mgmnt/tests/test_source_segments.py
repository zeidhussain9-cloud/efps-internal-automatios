from src.source_segments import split_source_messages


def test_timestamped_messages_are_kept_in_separate_source_units():
    raw = "[2026-09-15 10:01] Property Type: Semi Gated\n[2026-09-15 10:02] Furnishing: Semi Furnished"
    assert split_source_messages(raw) == ["Property Type: Semi Gated", "Furnishing: Semi Furnished"]


def test_plain_text_without_timestamps_remains_lossless_by_source_unit():
    raw = "2 BHK for rent\nSemi Furnished\n50000"
    assert split_source_messages(raw) == ["2 BHK for rent", "Semi Furnished", "50000"]

from src.source_consistency import extract_property_type, reconcile_property_type


def test_labelled_canonical_property_type_wins():
    raw = "Property Type: Semi Gated\n[2026-09-15 10:01] Furnishing: Semi Furnished"
    assert extract_property_type(raw) == "Semi Gated"


def test_gated_community_phrase_is_canonical():
    raw = "Gated Community\nRent: 50000"
    assert extract_property_type(raw) == "Gated Community"


def test_standalone_phrase_is_canonical():
    raw = "Property Type - Standalone\n2 BHK"
    assert extract_property_type(raw) == "Standalone"


def test_unrelated_type_word_does_not_classify():
    raw = "Type: Fully Furnished\n2 BHK for rent"
    assert extract_property_type(raw) == ""


def test_reconciliation_only_changes_when_source_is_explicit():
    row = {"internal_property_type": ""}
    assert reconcile_property_type(row, "Gated Community")['internal_property_type'] == "Gated Community"
    row = {"internal_property_type": "Semi Gated"}
    assert reconcile_property_type(row, "Type: Fully Furnished")['internal_property_type'] == "Semi Gated"

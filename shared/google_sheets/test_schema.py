from __future__ import annotations

import pytest

from . import schema


def test_contract_is_48_columns_a_to_av() -> None:
    assert schema.GRID_WIDTH == 48
    assert schema.LAST_COLUMN == "AV"
    assert schema.letter("listing_id") == "A"
    assert schema.letter("inventory_locked") == "AV"


def test_row_mapping_round_trip() -> None:
    row = [f"v{i}" for i in range(schema.GRID_WIDTH)]
    assert schema.mapping_to_row(schema.row_to_mapping(row)) == row


def test_row_width_is_enforced() -> None:
    with pytest.raises(ValueError):
        schema.validate_row(["only-one"])


def test_unknown_and_foreign_writes_are_rejected() -> None:
    with pytest.raises(KeyError):
        schema.mapping_to_row({"not_a_field": "x"})
    with pytest.raises(KeyError):
        schema.assert_writable(schema.PANEL, ["not_a_field"])
    with pytest.raises(PermissionError):
        schema.assert_writable(schema.PANEL, ["posted_url"])
    with pytest.raises(PermissionError):
        schema.assert_writable(schema.HOUSING_AGENT, ["listing_id"])

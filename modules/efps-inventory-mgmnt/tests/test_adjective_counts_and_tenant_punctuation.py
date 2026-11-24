import pytest
import extract
import normalize


@pytest.mark.parametrize("text,baths,balc", [
    ("*Fully Furnished 3 BHK with 4 Attached Bathrooms & 4 Balconies*", "4", "4"),
    ("*Semi Furnished 3 BHK with 3 Bathrooms, 2 Big Balconies & Utility*", "3", "2"),
    ("2 Spacious Attached Balconies", None, "2"),
    ("3 bathrooms", "3", None),
    ("3 BHK, 2 Baths", "2", None),
    ("3 BHK 2 Bathrooms 1 balcony", "2", "1"),
])
def test_counts_with_adjectives(text, baths, balc):
    out = extract.scan(text)
    assert out.get("bathrooms") == baths
    assert out.get("balconies") == balc


@pytest.mark.parametrize("text", ["no balcony", "2 BHK without balcony", "Floor: 3 Available from Ready bathrooms"])
def test_negative_or_unrelated_wording_gives_no_count(text):
    out = extract.scan(text)
    assert out.get("balconies") is None and out.get("bathrooms") is None


@pytest.mark.parametrize("value,expected", [
    ("Anyone.", "Open For All"), ("Anyone", "Open For All"), ("Open For All.", "Open For All"),
    ("Family Only,", "Family Only"), ("Family.", "Family Only"), ("", ""),
])
def test_tenant_trailing_punctuation(value, expected):
    assert normalize._canonical_tenant(value) == expected

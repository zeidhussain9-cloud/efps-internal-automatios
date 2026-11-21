

def test_catalog_title_always_rebuilt_from_dropdown_locality():
    # Locked owner rule (21 Nov 2026): the dropdown locality value is the
    # single place-name source for a property everywhere. A raw-text area
    # name that survived into catalog_title must be replaced.
    from normalize import build_catalog_title

    row = {"furnish_type": "Semi Furnished", "BHK": "1 BHK",
           "locality": "Haralur", "catalog_title": "Semi Furnished 1 BHK - Harlur"}
    assert build_catalog_title(row) == "Semi Furnished 1 BHK - Haralur"


def test_catalog_title_keeps_existing_only_when_no_locality():
    from normalize import build_catalog_title

    row = {"furnish_type": "", "BHK": "", "locality": "",
           "catalog_title": "Cozy Studio - Indiranagar"}
    assert build_catalog_title(row) == "Cozy Studio - Indiranagar"

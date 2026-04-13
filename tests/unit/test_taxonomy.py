from app.categorize.taxonomy import Taxonomy, load_default_taxonomy


def test_default_taxonomy_loads():
    tx = load_default_taxonomy()
    assert isinstance(tx, Taxonomy)
    assert len(tx.rules) > 0


def test_taxonomy_matches_swiggy():
    tx = load_default_taxonomy()
    hit = tx.match("upi/swiggy/12345")
    assert hit is not None
    assert hit.category == "food_delivery"
    assert hit.merchant == "Swiggy"


def test_taxonomy_matches_bescom():
    tx = load_default_taxonomy()
    hit = tx.match("neft bescom bill")
    assert hit is not None
    assert hit.category == "utilities"


def test_taxonomy_misses_unknown():
    tx = load_default_taxonomy()
    assert tx.match("random garbage no match") is None

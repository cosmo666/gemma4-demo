from datetime import date

from app.ledger.dedup import compute_dedup_key, normalize_description


def test_normalize_description_lowercases_and_collapses():
    assert normalize_description("  UPI/SWIGGY/   Ref 12345  ") == "upi/swiggy/ref"


def test_normalize_description_strips_ref_numbers():
    assert normalize_description("NEFT TRF ABC123456789") == "neft trf"


def test_compute_dedup_key_is_deterministic():
    k1 = compute_dedup_key(
        account_id=1,
        txn_date=date(2026, 2, 15),
        amount_paise=-15000,
        description_normalized="upi swiggy",
        within_day_counter=0,
    )
    k2 = compute_dedup_key(
        account_id=1,
        txn_date=date(2026, 2, 15),
        amount_paise=-15000,
        description_normalized="upi swiggy",
        within_day_counter=0,
    )
    assert k1 == k2
    assert len(k1) == 64


def test_compute_dedup_key_differs_with_counter():
    k1 = compute_dedup_key(1, date(2026, 2, 15), -15000, "upi swiggy", 0)
    k2 = compute_dedup_key(1, date(2026, 2, 15), -15000, "upi swiggy", 1)
    assert k1 != k2


def test_compute_dedup_key_differs_across_accounts():
    k1 = compute_dedup_key(1, date(2026, 2, 15), -15000, "upi swiggy", 0)
    k2 = compute_dedup_key(2, date(2026, 2, 15), -15000, "upi swiggy", 0)
    assert k1 != k2

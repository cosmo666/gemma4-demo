from datetime import date, datetime

from app.ledger.models import (
    Account,
    AuditLog,
    Bank,
    CategoryOverride,
    ConfigRow,
    Document,
    DocumentStatus,
    MerchantCanonical,
    RecurringSeries,
    Transaction,
)


def test_account_insert(session):
    a = Account(bank=Bank.SBI, account_number_masked="1234", holder_name="Prerak")
    session.add(a)
    session.commit()
    assert a.id is not None
    assert a.created_at is not None


def test_document_insert(session):
    a = Account(bank=Bank.HDFC, account_number_masked="9876", holder_name="Prerak")
    session.add(a)
    session.flush()
    d = Document(
        path="/tmp/x.pdf",
        file_sha256="a" * 64,
        bank=Bank.HDFC,
        account_id=a.id,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status=DocumentStatus.PENDING,
    )
    session.add(d)
    session.commit()
    assert d.id is not None
    assert d.status == DocumentStatus.PENDING
    assert d.txn_count_extracted == 0


def test_transaction_insert(session):
    a = Account(bank=Bank.SBI, account_number_masked="1111", holder_name="Prerak")
    session.add(a)
    session.flush()
    d = Document(
        path="/tmp/y.pdf",
        file_sha256="b" * 64,
        bank=Bank.SBI,
        account_id=a.id,
        period_start=date(2026, 2, 1),
        period_end=date(2026, 2, 28),
        status=DocumentStatus.APPROVED,
    )
    session.add(d)
    session.flush()
    t = Transaction(
        account_id=a.id,
        source_document_id=d.id,
        date=date(2026, 2, 15),
        amount_paise=-15000,
        description_raw="UPI/SWIGGY/...",
        description_normalized="upi swiggy",
        category="food_delivery",
        category_source="taxonomy",
        dedup_key="c" * 64,
        within_day_counter=0,
    )
    session.add(t)
    session.commit()
    assert t.id is not None
    assert isinstance(t.created_at, datetime)


def test_category_override(session):
    o = CategoryOverride(
        match_kind="exact_description",
        pattern="UPI/SWIGGY/12345",
        category="food_delivery",
    )
    session.add(o)
    session.commit()
    assert o.id is not None


def test_merchant_canonical(session):
    m = MerchantCanonical(
        raw_description_pattern="%swiggy%",
        canonical_name="Swiggy",
        category_hint="food_delivery",
    )
    session.add(m)
    session.commit()
    assert m.id is not None


def test_recurring_series(session):
    a = Account(bank=Bank.SBI, account_number_masked="2222", holder_name="P")
    session.add(a)
    session.flush()
    r = RecurringSeries(
        account_id=a.id,
        merchant_canonical="Netflix",
        category="subscriptions",
        cadence="monthly",
        typical_amount_paise=64900,
        confidence=0.95,
    )
    session.add(r)
    session.commit()
    assert r.id is not None
    assert r.active is True


def test_config_row(session):
    c = ConfigRow(
        age=26,
        dependents=0,
        annual_income_paise=60000000,
    )
    session.add(c)
    session.commit()
    assert c.one_off_threshold_paise == 1000000
    assert c.anomaly_multiplier == 2.0


def test_audit_log(session):
    a = AuditLog(
        event_type="ingest.classify",
        entity="document",
        entity_id="1",
        payload_json='{"bank":"sbi"}',
    )
    session.add(a)
    session.commit()
    assert a.id is not None

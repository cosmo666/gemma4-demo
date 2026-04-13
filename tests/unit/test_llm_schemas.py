from datetime import date

import pytest
from pydantic import ValidationError

from app.llm.schemas import (
    CategorizeItem,
    ClassifyDocument,
    ExtractHeader,
    ExtractTransaction,
)


def test_classify_document_ok():
    c = ClassifyDocument(
        bank="sbi",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        confidence=0.95,
        reason="SBI logo in header",
    )
    assert c.bank == "sbi"


def test_classify_document_bad_bank():
    with pytest.raises(ValidationError):
        ClassifyDocument(
            bank="icici",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            confidence=0.95,
            reason="",
        )


def test_extract_header_ok():
    h = ExtractHeader(
        account_number_masked="1234",
        holder_name="Prerak",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        opening_balance_paise=1000000,
        closing_balance_paise=900000,
    )
    assert h.opening_balance_paise == 1000000


def test_extract_transaction_rejects_float_amount():
    with pytest.raises(ValidationError):
        ExtractTransaction(
            date=date(2026, 1, 15),
            amount_paise=150.5,
            description_raw="x",
        )


def test_categorize_item_ok():
    c = CategorizeItem(index=0, category="food_delivery", confidence=0.9)
    assert c.index == 0

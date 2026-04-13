from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Bank = Literal["sbi", "hdfc", "unknown"]

Category = Literal[
    "rent",
    "utilities",
    "groceries",
    "food_delivery",
    "transport",
    "insurance_premium",
    "healthcare",
    "emi",
    "subscriptions",
    "shopping",
    "dining_out",
    "entertainment",
    "travel",
    "personal_care",
    "gifts_donations",
    "misc_discretionary",
    "income_salary",
    "income_other",
    "transfer_own",
    "investment_sip",
    "investment_other",
    "refund",
    "loan_received",
    "cash_withdrawal",
    "uncategorized",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class ClassifyDocument(StrictModel):
    bank: Bank
    period_start: date
    period_end: date
    confidence: float = Field(ge=0, le=1)
    reason: str


class ExtractHeader(StrictModel):
    account_number_masked: str
    holder_name: str
    period_start: date
    period_end: date
    opening_balance_paise: int
    closing_balance_paise: int


class ExtractTransaction(StrictModel):
    date: date
    amount_paise: int
    description_raw: str
    balance_after_paise: int | None = None


class CategorizeItem(StrictModel):
    index: int
    category: Category
    confidence: float = Field(ge=0, le=1)
    reason: str | None = None


class CanonicalMerchantItem(StrictModel):
    index: int
    canonical_name: str


class TextToSQL(StrictModel):
    sql: str
    explanation: str
    safety_check: Literal["select_only"]

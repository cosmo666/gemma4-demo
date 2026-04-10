import hashlib
import re
from datetime import date

_WHITESPACE = re.compile(r"\s+")
_LONG_DIGITS = re.compile(r"\S*\d{5,}\S*")
_REF_WORDS = re.compile(r"\s*(ref|txn|utr|rrn)\b[:\s]*\S*", re.IGNORECASE)


def normalize_description(raw: str) -> str:
    s = raw.strip().lower()
    # Remove long digit sequences first
    s = _LONG_DIGITS.sub("", s)
    # Replace ref/txn/etc words and their associated values with just the word
    s = _REF_WORDS.sub(r"\1", s)
    # Collapse multiple whitespace
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def compute_dedup_key(
    account_id: int,
    txn_date: date,
    amount_paise: int,
    description_normalized: str,
    within_day_counter: int,
) -> str:
    parts = [
        str(account_id),
        txn_date.isoformat(),
        str(amount_paise),
        description_normalized,
        str(within_day_counter),
    ]
    h = hashlib.sha256("|".join(parts).encode("utf-8"))
    return h.hexdigest()

# Foundations & UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Bank Statement Analyzer project with a SQLite ledger, Ollama client wrapper, audit log, taxonomy loader, and a polished FastAPI + Jinja2 + htmx UI shell (sidebar + topbar + sticky filter bar + empty-state dashboards) that runs cleanly at http://127.0.0.1:8765 with zero layout overlaps.

**Architecture:** Python 3.11 single-process FastAPI app. SQLAlchemy 2.0 models on SQLite with Alembic migrations. Jinja2 templates + self-hosted fonts + CSS Grid shell + htmx for interactions. No LLM calls wired up yet — only the Ollama client wrapper and pydantic schemas. This plan produces a working, navigable localhost app with empty states; subsequent plans fill in ingestion, categorization, and dashboards.

**Tech Stack:** Python 3.11, uv, FastAPI, SQLAlchemy 2.0, Alembic, pydantic v2, Jinja2, htmx 1.9, Chart.js 4 (loaded but unused in this plan), pytest, httpx (for test client), Fira Sans + Fira Code self-hosted.

---

## File Structure

```
gemma4-demo/
├── pyproject.toml                          # uv project config
├── .gitignore
├── .python-version
├── README.md                                # minimal: how to run
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── config.py                            # settings (paths, host, port)
│   ├── ledger/
│   │   ├── __init__.py
│   │   ├── base.py                          # SQLAlchemy Base + engine
│   │   ├── models.py                        # all ORM models
│   │   └── migrations/
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   │           └── 0001_initial.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                        # Ollama HTTP wrapper
│   │   ├── schemas.py                       # pydantic response schemas
│   │   └── prompts/                         # empty, populated later
│   ├── categorize/
│   │   ├── __init__.py
│   │   ├── taxonomy.py                      # YAML loader
│   │   └── taxonomy.yaml                    # merchant → category map
│   ├── audit/
│   │   ├── __init__.py
│   │   └── log.py                           # append-only JSONL + DB
│   └── web/
│       ├── __init__.py
│       ├── server.py                        # FastAPI app factory
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── dashboards.py
│       │   ├── review.py
│       │   ├── documents.py
│       │   ├── chat.py
│       │   └── config_page.py
│       ├── templates/
│       │   ├── base.html                    # shell layout
│       │   ├── _sidebar.html
│       │   ├── _topbar.html
│       │   ├── _filterbar.html
│       │   ├── dashboards/
│       │   │   ├── index.html
│       │   │   ├── _monthly.html
│       │   │   ├── _recurring.html
│       │   │   ├── _trends.html
│       │   │   └── _anomalies.html
│       │   ├── review.html
│       │   ├── documents.html
│       │   ├── chat.html
│       │   └── config.html
│       └── static/
│           ├── css/
│           │   ├── tokens.css                # design tokens (vars)
│           │   ├── base.css                  # reset + typography
│           │   ├── layout.css                # grid shell
│           │   └── components.css            # cards, buttons, tables
│           ├── js/
│           │   ├── htmx.min.js               # vendored
│           │   └── chart.min.js              # vendored
│           └── fonts/                        # Fira Sans + Fira Code
├── data/                                    # gitignored; created at runtime
│   ├── ledger.db
│   └── audit/
├── statements-inbox/                        # gitignored; user drops PDFs
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── test_models.py
    │   ├── test_dedup_key.py
    │   ├── test_llm_client.py
    │   ├── test_audit_log.py
    │   └── test_taxonomy.py
    └── web/
        └── test_routes_smoke.py
```

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `app/config.py`

- [ ] **Step 1: Create `.python-version`**

```
3.11
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "gemma4-demo"
version = "0.1.0"
description = "Local bank statement analyzer powered by Gemma 4 E4B"
requires-python = ">=3.11,<3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0.36",
    "alembic>=1.14",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "jinja2>=3.1",
    "python-multipart>=0.0.12",
    "httpx>=0.27",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "ruff>=0.7",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
ignore = ["E501"]
```

- [ ] **Step 3: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.pytest_cache/
.ruff_cache/
data/
statements-inbox/
*.db
*.db-journal
.env
```

- [ ] **Step 4: Create `README.md`**

```markdown
# gemma4-demo — Bank Statement Analyzer

Local, single-user tool that ingests SBI and HDFC bank statements and answers expense-analysis questions through four dashboards.

## Run

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.web.server:app --host 127.0.0.1 --port 8765 --reload
```

Open http://127.0.0.1:8765.

## Test

```bash
uv run pytest
```
```

- [ ] **Step 5: Create `app/__init__.py`**

```python
```

- [ ] **Step 6: Create `app/config.py`**

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8765

    data_dir: Path = ROOT / "data"
    audit_dir: Path = ROOT / "data" / "audit"
    inbox_dir: Path = ROOT / "statements-inbox"
    db_path: Path = ROOT / "data" / "ledger.db"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:e4b"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
```

- [ ] **Step 7: Install dependencies**

Run: `uv sync`
Expected: virtual env created under `.venv/`, lockfile generated.

- [ ] **Step 8: Commit**

```bash
git init
git add pyproject.toml .python-version .gitignore README.md app/__init__.py app/config.py
git commit -m "chore: project scaffold with uv and settings"
```

---

## Task 2: SQLAlchemy base and engine

**Files:**
- Create: `app/ledger/__init__.py`
- Create: `app/ledger/base.py`
- Test: `tests/__init__.py`, `tests/conftest.py`, `tests/unit/__init__.py`, `tests/unit/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/__init__.py` (empty), `tests/unit/__init__.py` (empty), then:

`tests/conftest.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ledger.base import Base


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
```

`tests/unit/test_models.py`:

```python
from app.ledger.base import Base


def test_base_metadata_exists():
    assert Base.metadata is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.ledger.base'`.

- [ ] **Step 3: Create `app/ledger/__init__.py` (empty)**

```python
```

- [ ] **Step 4: Create `app/ledger/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/ledger tests/
git commit -m "feat(ledger): SQLAlchemy declarative base"
```

---

## Task 3: Core ORM models (accounts, documents, transactions)

**Files:**
- Create: `app/ledger/models.py`
- Test: `tests/unit/test_models.py`

- [ ] **Step 1: Extend the failing test**

Replace `tests/unit/test_models.py` with:

```python
from datetime import date, datetime

from app.ledger.models import (
    Account,
    Bank,
    Document,
    DocumentStatus,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.ledger.models'`.

- [ ] **Step 3: Create `app/ledger/models.py`**

```python
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.ledger.base import Base


class Bank(str, enum.Enum):
    SBI = "sbi"
    HDFC = "hdfc"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    RECONCILING = "reconciling"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank: Mapped[Bank] = mapped_column(SAEnum(Bank), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(8), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="account")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    bank: Mapped[Bank | None] = mapped_column(SAEnum(Bank), nullable=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False
    )
    status_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    txn_count_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    txn_count_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    txn_count_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    account: Mapped[Account | None] = relationship(back_populates="documents")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="source_document")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_transactions_dedup_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_canonical: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category_source: Mapped[str] = mapped_column(String(16), nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    balance_after_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False)
    within_day_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    account: Mapped[Account] = relationship(back_populates="transactions")
    source_document: Mapped[Document] = relationship(back_populates="transactions")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: all 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ledger/models.py tests/unit/test_models.py
git commit -m "feat(ledger): core models — accounts, documents, transactions"
```

---

## Task 4: Supporting ORM models

**Files:**
- Modify: `app/ledger/models.py` (append)
- Test: `tests/unit/test_models.py` (append)

- [ ] **Step 1: Extend the failing test**

Append to `tests/unit/test_models.py`:

```python
from app.ledger.models import (
    AuditLog,
    CategoryOverride,
    ConfigRow,
    MerchantCanonical,
    RecurringSeries,
)


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
    from app.ledger.models import Account, Bank

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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: FAIL with ImportError on the new names.

- [ ] **Step 3: Append to `app/ledger/models.py`**

```python
class CategoryOverride(Base):
    __tablename__ = "category_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class MerchantCanonical(Base):
    __tablename__ = "merchant_canonical"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_description_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class RecurringSeries(Base):
    __tablename__ = "recurring_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    merchant_canonical: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    cadence: Mapped[str] = mapped_column(String(16), nullable=False)
    typical_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    typical_day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_seen: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_seen: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ConfigRow(Base):
    __tablename__ = "config"

    id: Mapped[int] = mapped_column(primary_key=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    dependents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annual_income_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    one_off_threshold_paise: Mapped[int] = mapped_column(
        Integer, default=1000000, nullable=False
    )
    leak_merchant_count_threshold: Mapped[int] = mapped_column(
        Integer, default=4, nullable=False
    )
    leak_merchant_amount_threshold_paise: Mapped[int] = mapped_column(
        Integer, default=5000000, nullable=False
    )
    anomaly_multiplier: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: all 8 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ledger/models.py tests/unit/test_models.py
git commit -m "feat(ledger): supporting models — overrides, recurring, config, audit"
```

---

## Task 5: Dedup key utility

**Files:**
- Create: `app/ledger/dedup.py`
- Test: `tests/unit/test_dedup_key.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_dedup_key.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_dedup_key.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/ledger/dedup.py`**

```python
import hashlib
import re
from datetime import date

_WHITESPACE = re.compile(r"\s+")
_LONG_DIGITS = re.compile(r"\b\d{5,}\b")
_REF_WORDS = re.compile(r"\b(ref|txn|utr|rrn)\b[:\s]*\S*", re.IGNORECASE)


def normalize_description(raw: str) -> str:
    s = raw.strip().lower()
    s = _REF_WORDS.sub("ref", s)
    s = _LONG_DIGITS.sub("", s)
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_dedup_key.py -v`
Expected: all 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ledger/dedup.py tests/unit/test_dedup_key.py
git commit -m "feat(ledger): deterministic dedup key and description normalizer"
```

---

## Task 6: Alembic setup and initial migration

**Files:**
- Create: `alembic.ini`
- Create: `app/ledger/migrations/env.py`
- Create: `app/ledger/migrations/script.py.mako`
- Create: `app/ledger/migrations/versions/0001_initial.py`

- [ ] **Step 1: Create `alembic.ini`**

```ini
[alembic]
script_location = app/ledger/migrations
sqlalchemy.url = sqlite:///data/ledger.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create `app/ledger/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 3: Create `app/ledger/migrations/env.py`**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.ledger.base import Base
from app.ledger import models  # noqa: F401 — register models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create data dir and generate migration**

```bash
mkdir -p data app/ledger/migrations/versions
uv run alembic revision --autogenerate -m "initial schema" --rev-id 0001
```

Expected: file `app/ledger/migrations/versions/0001_initial.py` created, containing `op.create_table(...)` calls for all 7 tables.

- [ ] **Step 5: Apply migration**

Run: `uv run alembic upgrade head`
Expected: `data/ledger.db` created with all tables. Log ends with `Running upgrade  -> 0001, initial schema`.

- [ ] **Step 6: Commit**

```bash
git add alembic.ini app/ledger/migrations/
git commit -m "feat(ledger): alembic setup and initial migration"
```

---

## Task 7: Pydantic LLM response schemas

**Files:**
- Create: `app/llm/__init__.py`
- Create: `app/llm/schemas.py`
- Test: `tests/unit/test_llm_schemas.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_llm_schemas.py`:

```python
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
            amount_paise=150.5,  # type: ignore[arg-type]
            description_raw="x",
        )


def test_categorize_item_ok():
    c = CategorizeItem(index=0, category="food_delivery", confidence=0.9)
    assert c.index == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_llm_schemas.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/llm/__init__.py` (empty)**

```python
```

- [ ] **Step 4: Create `app/llm/schemas.py`**

```python
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
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_llm_schemas.py -v`
Expected: all 5 PASS.

- [ ] **Step 6: Commit**

```bash
git add app/llm/ tests/unit/test_llm_schemas.py
git commit -m "feat(llm): pydantic response schemas for all tasks"
```

---

## Task 8: Ollama client wrapper

**Files:**
- Create: `app/llm/client.py`
- Test: `tests/unit/test_llm_client.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_llm_client.py`:

```python
import json

import httpx
import pytest

from app.llm.client import LLMClient, SchemaRetryError
from app.llm.schemas import ClassifyDocument


class FakeTransport(httpx.BaseTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def handle_request(self, request):
        self.calls.append(json.loads(request.content))
        body = self.responses.pop(0)
        return httpx.Response(200, json=body)


def _ollama_response(content: str) -> dict:
    return {"message": {"role": "assistant", "content": content}, "done": True}


def test_generate_structured_parses_valid_json():
    good = json.dumps(
        {
            "bank": "sbi",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "confidence": 0.9,
            "reason": "logo",
        }
    )
    transport = FakeTransport([_ollama_response(good)])
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    result = client.generate_structured(
        prompt="classify this", schema=ClassifyDocument, images=None
    )
    assert isinstance(result, ClassifyDocument)
    assert result.bank == "sbi"
    assert len(transport.calls) == 1


def test_generate_structured_retries_on_bad_json():
    bad = "not json at all"
    good = json.dumps(
        {
            "bank": "hdfc",
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "confidence": 0.8,
            "reason": "",
        }
    )
    transport = FakeTransport([_ollama_response(bad), _ollama_response(good)])
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    result = client.generate_structured(prompt="classify", schema=ClassifyDocument)
    assert result.bank == "hdfc"
    assert len(transport.calls) == 2


def test_generate_structured_raises_after_max_retries():
    transport = FakeTransport([_ollama_response("nope")] * 3)
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    with pytest.raises(SchemaRetryError):
        client.generate_structured(prompt="classify", schema=ClassifyDocument)
    assert len(transport.calls) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_llm_client.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/llm/client.py`**

```python
from __future__ import annotations

import json
import re
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


class SchemaRetryError(RuntimeError):
    pass


class LLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
        max_retries: int = 3,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=self._base_url, transport=transport, timeout=timeout
        )

    def close(self) -> None:
        self._client.close()

    def _chat(self, messages: list[dict], images: list[str] | None = None) -> str:
        payload = {"model": self._model, "messages": messages, "stream": False}
        if images:
            messages[-1]["images"] = images
        r = self._client.post("/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"]

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        images: list[str] | None = None,
        system: str | None = None,
    ) -> T:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        for _ in range(self._max_retries):
            try:
                content = self._chat(messages, images=images)
                obj = _extract_json(content)
                return schema.model_validate(obj)
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                last_error = e
        raise SchemaRetryError(f"schema validation failed after retries: {last_error}")


def _extract_json(text: str) -> dict:
    m = _JSON_BLOCK.search(text)
    if not m:
        raise ValueError(f"no JSON object in response: {text[:120]!r}")
    return json.loads(m.group(0))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_llm_client.py -v`
Expected: all 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/llm/client.py tests/unit/test_llm_client.py
git commit -m "feat(llm): Ollama client with schema retry"
```

---

## Task 9: Audit log

**Files:**
- Create: `app/audit/__init__.py`
- Create: `app/audit/log.py`
- Test: `tests/unit/test_audit_log.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_audit_log.py`:

```python
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.audit.log import AuditLogger
from app.ledger.models import AuditLog


def test_audit_logger_writes_db_and_jsonl(tmp_path: Path, engine):
    with Session(engine) as s:
        logger = AuditLogger(session=s, jsonl_dir=tmp_path)
        logger.emit(
            event_type="ingest.classify",
            entity="document",
            entity_id="7",
            payload={"bank": "sbi", "confidence": 0.92},
        )
        s.commit()

    with Session(engine) as s:
        rows = s.query(AuditLog).all()
        assert len(rows) == 1
        assert rows[0].event_type == "ingest.classify"
        assert json.loads(rows[0].payload_json)["bank"] == "sbi"

    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1
    line = files[0].read_text().strip()
    entry = json.loads(line)
    assert entry["event_type"] == "ingest.classify"
    assert entry["payload"]["confidence"] == 0.92
    assert "ts" in entry
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_audit_log.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/audit/__init__.py` (empty)**

```python
```

- [ ] **Step 4: Create `app/audit/log.py`**

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.ledger.models import AuditLog


class AuditLogger:
    def __init__(self, session: Session, jsonl_dir: Path) -> None:
        self._session = session
        self._jsonl_dir = jsonl_dir
        self._jsonl_dir.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        event_type: str,
        entity: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> None:
        ts = datetime.now(timezone.utc)
        payload_json = json.dumps(payload, sort_keys=True, default=str)

        row = AuditLog(
            event_type=event_type,
            entity=entity,
            entity_id=entity_id,
            payload_json=payload_json,
        )
        self._session.add(row)

        day = ts.strftime("%Y-%m-%d")
        file = self._jsonl_dir / f"{day}.jsonl"
        entry = {
            "ts": ts.isoformat(),
            "event_type": event_type,
            "entity": entity,
            "entity_id": entity_id,
            "payload": payload,
        }
        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_audit_log.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/audit/ tests/unit/test_audit_log.py
git commit -m "feat(audit): append-only audit log to DB and JSONL"
```

---

## Task 10: Taxonomy YAML loader

**Files:**
- Create: `app/categorize/__init__.py`
- Create: `app/categorize/taxonomy.yaml`
- Create: `app/categorize/taxonomy.py`
- Test: `tests/unit/test_taxonomy.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_taxonomy.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_taxonomy.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/categorize/__init__.py` (empty)**

```python
```

- [ ] **Step 4: Create `app/categorize/taxonomy.yaml`**

```yaml
rules:
  - pattern: swiggy
    merchant: Swiggy
    category: food_delivery
  - pattern: zomato
    merchant: Zomato
    category: food_delivery
  - pattern: blinkit
    merchant: Blinkit
    category: groceries
  - pattern: zepto
    merchant: Zepto
    category: groceries
  - pattern: bigbasket
    merchant: BigBasket
    category: groceries
  - pattern: dmart
    merchant: DMart
    category: groceries
  - pattern: uber
    merchant: Uber
    category: transport
  - pattern: ola
    merchant: Ola
    category: transport
  - pattern: rapido
    merchant: Rapido
    category: transport
  - pattern: irctc
    merchant: IRCTC
    category: travel
  - pattern: makemytrip
    merchant: MakeMyTrip
    category: travel
  - pattern: bescom
    merchant: BESCOM
    category: utilities
  - pattern: airtel
    merchant: Airtel
    category: utilities
  - pattern: jio
    merchant: Jio
    category: utilities
  - pattern: netflix
    merchant: Netflix
    category: subscriptions
  - pattern: spotify
    merchant: Spotify
    category: subscriptions
  - pattern: amazon prime
    merchant: Amazon Prime
    category: subscriptions
  - pattern: amazon
    merchant: Amazon
    category: shopping
  - pattern: flipkart
    merchant: Flipkart
    category: shopping
  - pattern: myntra
    merchant: Myntra
    category: shopping
  - pattern: apollo
    merchant: Apollo
    category: healthcare
  - pattern: practo
    merchant: Practo
    category: healthcare
  - pattern: lic
    merchant: LIC
    category: insurance_premium
  - pattern: salary
    merchant: null
    category: income_salary
  - pattern: atm
    merchant: null
    category: cash_withdrawal
```

- [ ] **Step 5: Create `app/categorize/taxonomy.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent / "taxonomy.yaml"


@dataclass(frozen=True)
class TaxonomyRule:
    pattern: str
    merchant: str | None
    category: str


@dataclass(frozen=True)
class TaxonomyHit:
    merchant: str | None
    category: str


class Taxonomy:
    def __init__(self, rules: list[TaxonomyRule]) -> None:
        self.rules = rules

    def match(self, description_normalized: str) -> TaxonomyHit | None:
        hay = description_normalized.lower()
        for rule in self.rules:
            if rule.pattern in hay:
                return TaxonomyHit(merchant=rule.merchant, category=rule.category)
        return None


def load_taxonomy(path: Path) -> Taxonomy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = [
        TaxonomyRule(
            pattern=r["pattern"].lower(),
            merchant=r.get("merchant"),
            category=r["category"],
        )
        for r in raw["rules"]
    ]
    return Taxonomy(rules)


def load_default_taxonomy() -> Taxonomy:
    return load_taxonomy(DEFAULT_PATH)
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/unit/test_taxonomy.py -v`
Expected: all 4 PASS.

- [ ] **Step 7: Commit**

```bash
git add app/categorize/ tests/unit/test_taxonomy.py
git commit -m "feat(categorize): taxonomy YAML and matcher"
```

---

## Task 11: FastAPI app factory and route stubs

**Files:**
- Create: `app/web/__init__.py`
- Create: `app/web/server.py`
- Create: `app/web/routes/__init__.py`
- Create: `app/web/routes/dashboards.py`
- Create: `app/web/routes/review.py`
- Create: `app/web/routes/documents.py`
- Create: `app/web/routes/chat.py`
- Create: `app/web/routes/config_page.py`
- Test: `tests/web/__init__.py`, `tests/web/test_routes_smoke.py`

- [ ] **Step 1: Write the failing test**

`tests/web/__init__.py` (empty).

`tests/web/test_routes_smoke.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.web.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/dashboards",
        "/review",
        "/documents",
        "/chat",
        "/config",
    ],
)
def test_route_returns_200_and_html(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Expense Lens" in r.text


def test_static_css_tokens_served(client):
    r = client.get("/static/css/tokens.css")
    assert r.status_code == 200
    assert "--color-primary" in r.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/web/ -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Create `app/web/__init__.py` (empty)**

```python
```

- [ ] **Step 4: Create `app/web/routes/__init__.py`**

```python
from fastapi import APIRouter

from app.web.routes import chat, config_page, dashboards, documents, review

router = APIRouter()
router.include_router(dashboards.router)
router.include_router(review.router)
router.include_router(documents.router)
router.include_router(chat.router)
router.include_router(config_page.router)
```

- [ ] **Step 5: Create `app/web/routes/dashboards.py`**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboards", response_class=HTMLResponse)
async def dashboards(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboards/index.html",
        {"active": "dashboards", "page_title": "Dashboards"},
    )
```

- [ ] **Step 6: Create `app/web/routes/review.py`**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/review", response_class=HTMLResponse)
async def review(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "review.html",
        {"active": "review", "page_title": "Review queue", "pending_count": 0},
    )
```

- [ ] **Step 7: Create `app/web/routes/documents.py`**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/documents", response_class=HTMLResponse)
async def documents(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "documents.html",
        {"active": "documents", "page_title": "Documents"},
    )
```

- [ ] **Step 8: Create `app/web/routes/chat.py`**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "page_title": "Chat"},
    )
```

- [ ] **Step 9: Create `app/web/routes/config_page.py`**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/config", response_class=HTMLResponse)
async def config_view(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "config.html",
        {"active": "config", "page_title": "Config"},
    )
```

- [ ] **Step 10: Create `app/web/server.py`**

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app() -> FastAPI:
    settings.ensure_dirs()
    app = FastAPI(title="Expense Lens", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    from app.web.routes import router

    app.include_router(router)
    return app


app = create_app()
```

- [ ] **Step 11: Create empty static dirs so mount doesn't fail**

Run:

```bash
mkdir -p app/web/static/css app/web/static/js app/web/static/fonts app/web/templates/dashboards
```

- [ ] **Step 12: Commit**

```bash
git add app/web/
git commit -m "feat(web): FastAPI scaffold and route stubs"
```

Tests still fail because templates and CSS don't exist. That's the next tasks.

---

## Task 12: Design tokens and base CSS

**Files:**
- Create: `app/web/static/css/tokens.css`
- Create: `app/web/static/css/base.css`

- [ ] **Step 1: Create `app/web/static/css/tokens.css`**

```css
:root {
  /* colors */
  --color-primary: #2563EB;
  --color-primary-600: #1D4ED8;
  --color-accent: #F97316;
  --color-bg: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-surface-hover: #F1F5F9;
  --color-border: #E2E8F0;
  --color-border-strong: #CBD5E1;
  --color-text: #1E293B;
  --color-text-muted: #64748B;
  --color-success: #16A34A;
  --color-warning: #F59E0B;
  --color-danger: #DC2626;
  --color-neutral-grid: #E2E8F0;

  /* radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* spacing (4pt scale) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* shadows */
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px rgb(0 0 0 / 0.07);
  --shadow-lg: 0 10px 15px rgb(0 0 0 / 0.10);

  /* motion */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);

  /* layout */
  --shell-topbar-h: 64px;
  --shell-filterbar-h: 56px;
  --shell-sidebar-w: 240px;
  --shell-sidebar-w-collapsed: 64px;
  --shell-content-max: 1440px;
  --z-topbar: 30;
  --z-filterbar: 20;
  --z-sidebar: 40;
  --z-modal: 100;

  /* typography */
  --font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'Fira Code', 'SFMono-Regular', Consolas, monospace;
}
```

- [ ] **Step 2: Create `app/web/static/css/base.css`**

```css
*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
}

body {
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

h1, h2, h3, h4, h5, h6 {
  margin: 0;
  line-height: 1.2;
  font-weight: 600;
  letter-spacing: -0.01em;
}

h1 { font-size: 32px; }
h2 { font-size: 24px; }
h3 { font-size: 18px; }
h4 { font-size: 16px; }

p { margin: 0; }

a {
  color: var(--color-primary);
  text-decoration: none;
}
a:hover { text-decoration: underline; }

button {
  font-family: inherit;
  font-size: inherit;
  cursor: pointer;
}

:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

.muted { color: var(--color-text-muted); }
.success { color: var(--color-success); }
.warning { color: var(--color-warning); }
.danger { color: var(--color-danger); }

.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add app/web/static/css/tokens.css app/web/static/css/base.css
git commit -m "feat(web): design tokens and base typography"
```

---

## Task 13: Layout shell CSS (no-overlap grid)

**Files:**
- Create: `app/web/static/css/layout.css`

- [ ] **Step 1: Create `app/web/static/css/layout.css`**

The shell uses CSS Grid with named areas. Sidebar spans all rows; topbar and filterbar occupy fixed-height rows; main scrolls independently. This structurally prevents overlap — each region has its own cell.

```css
.shell {
  display: grid;
  grid-template-columns: var(--shell-sidebar-w) minmax(0, 1fr);
  grid-template-rows: var(--shell-topbar-h) var(--shell-filterbar-h) minmax(0, 1fr);
  grid-template-areas:
    "sidebar topbar"
    "sidebar filterbar"
    "sidebar main";
  height: 100vh;
  width: 100%;
}

.shell__sidebar {
  grid-area: sidebar;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: var(--z-sidebar);
  min-width: 0;
  overflow-y: auto;
}

.shell__topbar {
  grid-area: topbar;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  z-index: var(--z-topbar);
  gap: var(--space-4);
  min-width: 0;
}

.shell__filterbar {
  grid-area: filterbar;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  gap: var(--space-3);
  z-index: var(--z-filterbar);
  min-width: 0;
}

.shell__main {
  grid-area: main;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
  min-height: 0;
  padding: var(--space-6);
}

.shell__main-inner {
  max-width: var(--shell-content-max);
  margin: 0 auto;
}

/* sidebar nav */
.nav {
  display: flex;
  flex-direction: column;
  padding: var(--space-4) var(--space-2);
  gap: var(--space-1);
}

.nav__brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-3) var(--space-4);
  font-weight: 600;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.nav__brand-mark {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  flex-shrink: 0;
}

.nav__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-weight: 500;
  transition: background var(--duration-fast) var(--ease-out),
              color var(--duration-fast) var(--ease-out);
  position: relative;
  min-width: 0;
}
.nav__item:hover {
  background: var(--color-surface-hover);
  text-decoration: none;
}
.nav__item--active {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
}
.nav__item--active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}
.nav__icon { width: 18px; height: 18px; flex-shrink: 0; }
.nav__label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nav__badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--color-accent);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: grid;
  place-items: center;
}

.nav__spacer { flex: 1; }
.nav__footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 12px;
}

/* topbar */
.topbar__title {
  font-size: 18px;
  font-weight: 600;
}
.topbar__spacer { flex: 1; }
.topbar__action {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  transition: background var(--duration-fast) var(--ease-out);
}
.topbar__action:hover { background: var(--color-surface-hover); }

/* filter bar */
.filterbar__group {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: 14px;
  min-width: 0;
}
.filterbar__label {
  color: var(--color-text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.filterbar__spacer { flex: 1; }

/* responsive: collapse sidebar below 1024 */
@media (max-width: 1024px) {
  .shell {
    grid-template-columns: var(--shell-sidebar-w-collapsed) minmax(0, 1fr);
  }
  .nav__label,
  .nav__badge,
  .nav__brand span:not(.nav__brand-mark) {
    display: none;
  }
  .nav__item { justify-content: center; padding: var(--space-3) 0; }
}

@media (max-width: 640px) {
  .shell__main { padding: var(--space-4); }
  .shell__topbar, .shell__filterbar { padding: 0 var(--space-4); }
}
```

- [ ] **Step 2: Commit**

```bash
git add app/web/static/css/layout.css
git commit -m "feat(web): CSS grid shell with no-overlap layout"
```

---

## Task 14: Component CSS (cards, buttons, tables, empty states)

**Files:**
- Create: `app/web/static/css/components.css`

- [ ] **Step 1: Create `app/web/static/css/components.css`**

```css
/* cards */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--space-5);
  min-width: 0;
}
.card + .card { margin-top: var(--space-4); }

.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  gap: var(--space-3);
}
.card__title { font-size: 16px; font-weight: 600; }
.card__subtitle { color: var(--color-text-muted); font-size: 13px; }

/* grid for dashboard rows */
.grid {
  display: grid;
  gap: var(--space-6);
}
.grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-1 { grid-template-columns: minmax(0, 1fr); }
@media (max-width: 1024px) {
  .grid-cols-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .grid-cols-4, .grid-cols-2 { grid-template-columns: minmax(0, 1fr); }
}

/* KPI */
.kpi__label {
  color: var(--color-text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}
.kpi__value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--color-text);
}
.kpi__delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: var(--space-2);
  font-size: 12px;
  font-weight: 500;
}
.kpi__delta--up { color: var(--color-danger); }
.kpi__delta--down { color: var(--color-success); }

/* buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 40px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-weight: 500;
  font-size: 14px;
  transition:
    background var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
  min-width: 44px;
  min-height: 44px;
}
.btn:active { transform: scale(0.98); }
.btn--primary {
  background: var(--color-primary);
  color: #fff;
}
.btn--primary:hover { background: var(--color-primary-600); }
.btn--accent {
  background: var(--color-accent);
  color: #fff;
}
.btn--accent:hover { filter: brightness(0.95); }
.btn--ghost {
  background: transparent;
  border-color: var(--color-border);
  color: var(--color-text);
}
.btn--ghost:hover { background: var(--color-surface-hover); }
.btn[disabled] { opacity: 0.5; cursor: not-allowed; }

/* tables */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.table thead th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  position: sticky;
  top: 0;
}
.table tbody td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}
.table tbody tr:hover { background: var(--color-surface-hover); }
.table td.num, .table th.num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

/* empty state */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-12) var(--space-6);
  min-height: 300px;
  color: var(--color-text-muted);
}
.empty__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--color-surface-hover);
  display: grid;
  place-items: center;
  margin-bottom: var(--space-4);
  color: var(--color-text-muted);
}
.empty__title {
  color: var(--color-text);
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--space-2);
}
.empty__body {
  max-width: 420px;
  margin-bottom: var(--space-5);
}

/* tabs */
.tabs {
  display: flex;
  gap: var(--space-1);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
  overflow-x: auto;
}
.tab {
  padding: var(--space-3) var(--space-4);
  font-weight: 500;
  color: var(--color-text-muted);
  border-bottom: 2px solid transparent;
  transition: color var(--duration-fast) var(--ease-out),
              border-color var(--duration-fast) var(--ease-out);
  white-space: nowrap;
  background: transparent;
  border-top: 0; border-left: 0; border-right: 0;
}
.tab:hover { color: var(--color-text); }
.tab--active { color: var(--color-primary); border-bottom-color: var(--color-primary); }

/* chip */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 22px;
  padding: 0 var(--space-2);
  border-radius: 11px;
  font-size: 12px;
  font-weight: 500;
  background: var(--color-surface-hover);
  color: var(--color-text-muted);
}
.chip--success { background: color-mix(in srgb, var(--color-success) 12%, transparent); color: var(--color-success); }
.chip--warning { background: color-mix(in srgb, var(--color-warning) 14%, transparent); color: #B45309; }
.chip--danger { background: color-mix(in srgb, var(--color-danger) 12%, transparent); color: var(--color-danger); }

/* coverage strip */
.coverage-warning {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  background: color-mix(in srgb, var(--color-warning) 14%, var(--color-surface));
  border: 1px solid color-mix(in srgb, var(--color-warning) 40%, transparent);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  color: #92400E;
  font-size: 14px;
  margin-bottom: var(--space-5);
}

/* section header */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-5);
  gap: var(--space-4);
}
.section-header h2 { font-size: 20px; }
```

- [ ] **Step 2: Commit**

```bash
git add app/web/static/css/components.css
git commit -m "feat(web): component styles — cards, buttons, tables, empty states"
```

---

## Task 15: Base template, sidebar, topbar, filter bar

**Files:**
- Create: `app/web/templates/base.html`
- Create: `app/web/templates/_sidebar.html`
- Create: `app/web/templates/_topbar.html`
- Create: `app/web/templates/_filterbar.html`

- [ ] **Step 1: Create `app/web/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ page_title }} · Expense Lens</title>
  <link rel="stylesheet" href="/static/css/tokens.css">
  <link rel="stylesheet" href="/static/css/base.css">
  <link rel="stylesheet" href="/static/css/layout.css">
  <link rel="stylesheet" href="/static/css/components.css">
  <style>
    /* inline: system font fallback until fonts are added */
  </style>
</head>
<body>
  <div class="shell">
    {% include "_sidebar.html" %}
    {% include "_topbar.html" %}
    {% block filterbar %}{% include "_filterbar.html" %}{% endblock %}
    <main class="shell__main" id="main">
      <div class="shell__main-inner">
        {% block main %}{% endblock %}
      </div>
    </main>
  </div>
  <script src="/static/js/htmx.min.js" defer></script>
  <script src="/static/js/chart.min.js" defer></script>
</body>
</html>
```

- [ ] **Step 2: Create `app/web/templates/_sidebar.html`**

```html
<aside class="shell__sidebar" aria-label="Primary">
  <nav class="nav" aria-label="Main navigation">
    <div class="nav__brand">
      <span class="nav__brand-mark" aria-hidden="true">E</span>
      <span>Expense Lens</span>
    </div>

    <a href="/dashboards" class="nav__item {% if active == 'dashboards' %}nav__item--active{% endif %}">
      <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
        <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
      </svg>
      <span class="nav__label">Dashboards</span>
    </a>

    <a href="/review" class="nav__item {% if active == 'review' %}nav__item--active{% endif %}">
      <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
      <span class="nav__label">Review queue</span>
      {% if pending_count and pending_count > 0 %}
      <span class="nav__badge">{{ pending_count }}</span>
      {% endif %}
    </a>

    <a href="/documents" class="nav__item {% if active == 'documents' %}nav__item--active{% endif %}">
      <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <span class="nav__label">Documents</span>
    </a>

    <a href="/chat" class="nav__item {% if active == 'chat' %}nav__item--active{% endif %}">
      <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span class="nav__label">Chat</span>
    </a>

    <div class="nav__spacer"></div>

    <a href="/config" class="nav__item {% if active == 'config' %}nav__item--active{% endif %}">
      <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
      <span class="nav__label">Config</span>
    </a>
    <div class="nav__footer">v0.1.0 · local</div>
  </nav>
</aside>
```

- [ ] **Step 2: Create `app/web/templates/_topbar.html`**

```html
<header class="shell__topbar" role="banner">
  <h1 class="topbar__title">{{ page_title }}</h1>
  <div class="topbar__spacer"></div>
  <button class="topbar__action" type="button" aria-label="Upload statement">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
    <span>Upload</span>
  </button>
</header>
```

- [ ] **Step 3: Create `app/web/templates/_filterbar.html`**

```html
<div class="shell__filterbar" role="region" aria-label="Filters">
  <div class="filterbar__group">
    <span class="filterbar__label">Range</span>
    <span>This month</span>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
  </div>
  <div class="filterbar__group">
    <span class="filterbar__label">Accounts</span>
    <span>SBI + HDFC</span>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
  </div>
  <div class="filterbar__spacer"></div>
  <span class="muted" style="font-size:12px;">Data through — no statements ingested yet</span>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add app/web/templates/base.html app/web/templates/_sidebar.html app/web/templates/_topbar.html app/web/templates/_filterbar.html
git commit -m "feat(web): base template, sidebar, topbar, filter bar"
```

---

## Task 16: Dashboards page with 4 empty-state sections

**Files:**
- Create: `app/web/templates/dashboards/index.html`
- Create: `app/web/templates/dashboards/_monthly.html`
- Create: `app/web/templates/dashboards/_recurring.html`
- Create: `app/web/templates/dashboards/_trends.html`
- Create: `app/web/templates/dashboards/_anomalies.html`

- [ ] **Step 1: Create `app/web/templates/dashboards/index.html`**

```html
{% extends "base.html" %}

{% block main %}
<div class="tabs" role="tablist" aria-label="Dashboards">
  <button class="tab tab--active" role="tab" aria-selected="true" data-tab="monthly">Monthly overview</button>
  <button class="tab" role="tab" aria-selected="false" data-tab="recurring">Recurring vs one-time</button>
  <button class="tab" role="tab" aria-selected="false" data-tab="trends">Trends &amp; leaks</button>
  <button class="tab" role="tab" aria-selected="false" data-tab="anomalies">Anomalies</button>
</div>

<section data-panel="monthly">{% include "dashboards/_monthly.html" %}</section>
<section data-panel="recurring" hidden>{% include "dashboards/_recurring.html" %}</section>
<section data-panel="trends" hidden>{% include "dashboards/_trends.html" %}</section>
<section data-panel="anomalies" hidden>{% include "dashboards/_anomalies.html" %}</section>

<script>
  // Tab switching — minimal vanilla JS, no framework dependency
  (function () {
    const tabs = document.querySelectorAll('.tab[data-tab]');
    const panels = document.querySelectorAll('section[data-panel]');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => {
          t.classList.toggle('tab--active', t === tab);
          t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
        });
        const target = tab.dataset.tab;
        panels.forEach(p => {
          p.hidden = p.dataset.panel !== target;
        });
      });
    });
  })();
</script>
{% endblock %}
```

- [ ] **Step 2: Create `app/web/templates/dashboards/_monthly.html`**

```html
<div class="grid grid-cols-4">
  <div class="card">
    <div class="kpi__label">Real monthly burn</div>
    <div class="kpi__value">—</div>
    <div class="kpi__delta muted">awaiting data</div>
  </div>
  <div class="card">
    <div class="kpi__label">Total spend</div>
    <div class="kpi__value">—</div>
    <div class="kpi__delta muted">0 transactions</div>
  </div>
  <div class="card">
    <div class="kpi__label">One-offs excluded</div>
    <div class="kpi__value">—</div>
    <div class="kpi__delta muted">0 items</div>
  </div>
  <div class="card">
    <div class="kpi__label">Net position</div>
    <div class="kpi__value">—</div>
    <div class="kpi__delta muted">income − expense</div>
  </div>
</div>

<div class="grid grid-cols-2" style="margin-top: var(--space-6);">
  <div class="card">
    <div class="card__header">
      <div>
        <div class="card__title">Category breakdown</div>
        <div class="card__subtitle">Horizontal bars, direct-labeled</div>
      </div>
    </div>
    <div class="empty" style="min-height:220px;">
      <div class="empty__icon" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
      </div>
      <div class="empty__title">No spend to chart yet</div>
      <div class="empty__body">Ingest a bank statement to see your category breakdown.</div>
    </div>
  </div>
  <div class="card">
    <div class="card__header">
      <div>
        <div class="card__title">Income vs expense</div>
        <div class="card__subtitle">Bullet chart</div>
      </div>
    </div>
    <div class="empty" style="min-height:220px;">
      <div class="empty__icon" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
      </div>
      <div class="empty__title">Waiting for statements</div>
      <div class="empty__body">Your net position will appear once income and expenses are recorded.</div>
    </div>
  </div>
</div>

<div class="card" style="margin-top: var(--space-6);">
  <div class="card__header">
    <div>
      <div class="card__title">Recent transactions</div>
      <div class="card__subtitle">Last 50, sorted by date</div>
    </div>
  </div>
  <div class="empty">
    <div class="empty__title">Nothing here yet</div>
    <div class="empty__body">Drop a PDF into <code>statements-inbox/</code> or click Upload to get started.</div>
    <a class="btn btn--accent" href="/review">Upload a statement</a>
  </div>
</div>
```

- [ ] **Step 3: Create `app/web/templates/dashboards/_recurring.html`**

```html
<div class="grid grid-cols-2">
  <div class="card">
    <div class="card__header">
      <div>
        <div class="card__title">Every month</div>
        <div class="card__subtitle">Detected recurring series</div>
      </div>
    </div>
    <div class="empty">
      <div class="empty__title">No recurring payments detected</div>
      <div class="empty__body">Recurring detection needs at least 3 months of history per merchant.</div>
    </div>
  </div>
  <div class="card">
    <div class="card__header">
      <div>
        <div class="card__title">One-time this month</div>
        <div class="card__subtitle">Top 10 by amount</div>
      </div>
    </div>
    <div class="empty">
      <div class="empty__title">Nothing to show</div>
      <div class="empty__body">One-time expenses will appear here after your first statement is ingested.</div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: Create `app/web/templates/dashboards/_trends.html`**

```html
<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">Category trend</div>
      <div class="card__subtitle">Month-over-month per category</div>
    </div>
  </div>
  <div class="empty" style="min-height:280px;">
    <div class="empty__title">Need at least 2 months of data</div>
    <div class="empty__body">Trends appear once multiple months have been ingested.</div>
  </div>
</div>

<div class="grid grid-cols-2" style="margin-top: var(--space-6);">
  <div class="card">
    <div class="card__header"><div class="card__title">Diff vs last month</div></div>
    <div class="empty"><div class="empty__title">No comparison available</div></div>
  </div>
  <div class="card">
    <div class="card__header"><div class="card__title">Merchant search</div></div>
    <div class="empty"><div class="empty__title">Search disabled until data is loaded</div></div>
  </div>
</div>

<div class="card" style="margin-top: var(--space-6);">
  <div class="card__header">
    <div>
      <div class="card__title">Small-frequent leaks</div>
      <div class="card__subtitle">≥4 hits, average &lt; ₹500</div>
    </div>
  </div>
  <div class="empty"><div class="empty__title">No leaks detected yet</div></div>
</div>
```

- [ ] **Step 5: Create `app/web/templates/dashboards/_anomalies.html`**

```html
<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">Anomalies this month</div>
      <div class="card__subtitle">≥2× rolling 3-month median</div>
    </div>
  </div>
  <div class="empty" style="min-height:300px;">
    <div class="empty__icon" aria-hidden="true">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 22h20L12 2z"/><line x1="12" y1="9" x2="12" y2="14"/><circle cx="12" cy="17.5" r="0.8" fill="currentColor"/></svg>
    </div>
    <div class="empty__title">Insufficient history</div>
    <div class="empty__body">Anomaly detection needs at least 3 full months of ingested data. You currently have 0 months.</div>
  </div>
</div>
```

- [ ] **Step 6: Commit**

```bash
git add app/web/templates/dashboards/
git commit -m "feat(web): dashboards page with 4 empty-state sections and tabs"
```

---

## Task 17: Remaining page templates (review, documents, chat, config)

**Files:**
- Create: `app/web/templates/review.html`
- Create: `app/web/templates/documents.html`
- Create: `app/web/templates/chat.html`
- Create: `app/web/templates/config.html`

- [ ] **Step 1: Create `app/web/templates/review.html`**

```html
{% extends "base.html" %}

{% block main %}
<div class="section-header">
  <h2>Review queue</h2>
  <span class="chip">{{ pending_count }} pending</span>
</div>

<div class="card">
  <div class="empty">
    <div class="empty__icon" aria-hidden="true">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    </div>
    <div class="empty__title">Nothing to review</div>
    <div class="empty__body">Drop PDFs into <code>statements-inbox/</code> to process them. They'll appear here once classified and extracted.</div>
    <button class="btn btn--accent" type="button">Upload statement</button>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Create `app/web/templates/documents.html`**

```html
{% extends "base.html" %}

{% block main %}
<div class="section-header">
  <h2>Documents</h2>
</div>

<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">Coverage map</div>
      <div class="card__subtitle">Per-account month coverage</div>
    </div>
  </div>
  <div class="empty">
    <div class="empty__title">No accounts yet</div>
    <div class="empty__body">Upload a statement to start building your coverage map.</div>
  </div>
</div>

<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">All processed documents</div>
    </div>
  </div>
  <div class="empty">
    <div class="empty__title">No documents yet</div>
    <div class="empty__body">Files you process will appear here with their status and counts.</div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Create `app/web/templates/chat.html`**

```html
{% extends "base.html" %}

{% block main %}
<div class="section-header">
  <h2>Ask anything</h2>
  <span class="muted" style="font-size:13px;">Text-to-SQL · select-only · read-only connection</span>
</div>

<div class="card">
  <div class="empty">
    <div class="empty__icon" aria-hidden="true">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    </div>
    <div class="empty__title">Chat is offline until ingestion works</div>
    <div class="empty__body">Once statements are ingested, ask things like "What's my Swiggy total this quarter?" or "Top 5 merchants last month?"</div>
  </div>
  <div class="grid grid-cols-1" style="gap: var(--space-2); margin-top: var(--space-5);">
    <button class="btn btn--ghost" type="button" disabled>What's my burn?</button>
    <button class="btn btn--ghost" type="button" disabled>Top 5 merchants?</button>
    <button class="btn btn--ghost" type="button" disabled>Swiggy total this year?</button>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Create `app/web/templates/config.html`**

```html
{% extends "base.html" %}

{% block main %}
<div class="section-header">
  <h2>Config</h2>
</div>

<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">Owner profile</div>
      <div class="card__subtitle">Used for display; no adequacy checks in v1</div>
    </div>
  </div>
  <div class="empty">
    <div class="empty__title">Profile editor coming next</div>
    <div class="empty__body">Age, dependents, annual income, and thresholds will be editable here.</div>
  </div>
</div>

<div class="card">
  <div class="card__header">
    <div>
      <div class="card__title">Thresholds</div>
      <div class="card__subtitle">One-off, leak, anomaly multiplier</div>
    </div>
  </div>
  <div class="empty">
    <div class="empty__title">No config loaded yet</div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add app/web/templates/review.html app/web/templates/documents.html app/web/templates/chat.html app/web/templates/config.html
git commit -m "feat(web): review, documents, chat, config page templates"
```

---

## Task 18: Vendor htmx and Chart.js; create stub JS

**Files:**
- Create: `app/web/static/js/htmx.min.js` (placeholder — stub content so tests pass without network)
- Create: `app/web/static/js/chart.min.js` (placeholder)

- [ ] **Step 1: Create placeholder `app/web/static/js/htmx.min.js`**

For plan 1 we don't need functional htmx yet — the templates don't use it. A stub file lets the static mount work and the `<script>` tags load without 404. Real vendoring happens in a later plan when htmx interactions are introduced.

```javascript
// Placeholder for htmx 1.9 — will be vendored in a later plan when first used.
// This file exists so static/js/htmx.min.js resolves without a 404.
```

- [ ] **Step 2: Create placeholder `app/web/static/js/chart.min.js`**

```javascript
// Placeholder for Chart.js 4 — will be vendored when the first chart ships.
```

- [ ] **Step 3: Commit**

```bash
git add app/web/static/js/
git commit -m "chore(web): placeholder JS vendors"
```

---

## Task 19: Run smoke tests and manually verify the UI shell

- [ ] **Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: every test passes. The smoke tests from Task 11 should now succeed because templates, CSS, and routes all exist.

- [ ] **Step 2: Start the app**

Run: `uv run uvicorn app.web.server:app --host 127.0.0.1 --port 8765`
Expected: server starts, logs `Uvicorn running on http://127.0.0.1:8765`.

- [ ] **Step 3: Manual UI verification checklist**

Open `http://127.0.0.1:8765` in a browser and verify each item. Do not proceed to commit until every box is checked.

- [ ] Sidebar is 240px wide and does not overlap the topbar, filter bar, or main content at any viewport width.
- [ ] Topbar and filter bar are full width of the main column, stacked vertically, no overlap.
- [ ] Main scroll region scrolls independently — sidebar, topbar, and filter bar stay in place while main scrolls.
- [ ] Every nav item is clickable and routes to the right page; the active item shows the blue left-rail highlight and the `--color-primary` text color.
- [ ] Dashboards page shows the 4 tabs; clicking each tab swaps the panel without page reload; no two panels are visible at once.
- [ ] Monthly Overview panel shows 4 KPI cards in a row on ≥1024px, collapses to 2 columns on ~768px, and to 1 column on ~375px.
- [ ] No horizontal scroll at any viewport from 375px to 1920px.
- [ ] All empty states show their title, body text, and (where present) their CTA button without clipping.
- [ ] Focus ring is visible when tabbing through nav items and buttons (keyboard only).
- [ ] Zoom to 200% in the browser — layout still holds, no overlap, no text clipped.

- [ ] **Step 4: If any checklist item fails**

Fix it in the relevant CSS / template file before committing. Do not commit a broken shell. If the fix touches multiple files, make one focused commit per fix.

- [ ] **Step 5: Commit the verification record**

Only once every checkbox above is checked, add a brief note to README.md under a new "Status" section:

```markdown
## Status

- [x] Foundations: models, migrations, LLM client, audit log, taxonomy
- [x] UI shell: sidebar + topbar + filter bar + empty-state dashboards
- [ ] Ingestion pipeline
- [ ] Categorization
- [ ] Dashboard 1: Monthly Overview
- [ ] Dashboard 2: Recurring vs One-Time
- [ ] Dashboard 3: Trends & Leaks
- [ ] Dashboard 4: Anomalies
- [ ] Chat (text-to-SQL)
```

Then:

```bash
git add README.md
git commit -m "docs: mark plan 1 (foundations + UI shell) complete"
```

---

## Plan summary

After executing this plan, you will have:

- A `uv`-managed Python project with all core dependencies pinned via lockfile.
- A complete SQLite schema via Alembic: accounts, documents, transactions (with dedup_key unique constraint), category_overrides, merchant_canonical, recurring_series, config, audit_log.
- A deterministic dedup key utility with tests covering determinism, counter, and cross-account variance.
- A pydantic-typed Ollama client with schema retry (tested with a fake transport — no live Ollama required).
- An append-only audit logger that writes both to SQLite and JSONL files on disk.
- A YAML-backed taxonomy loader with ~25 seed rules covering common Indian merchants.
- A FastAPI app mounted at `127.0.0.1:8765` with 6 routes returning clean HTML shells.
- Jinja2 templates with a CSS-Grid shell (sidebar + topbar + filter bar + scrollable main) that structurally cannot overlap, empty states for every screen, responsive breakpoints at 1024/640, and full keyboard accessibility.
- A smoke test suite verifying every route returns 200 HTML and CSS tokens are served.
- A visible, navigable app the owner can open in a browser immediately.

The next plan picks up with the ingestion pipeline: PDF → classify → extract header → extract transactions → dedupe → insert → review queue.

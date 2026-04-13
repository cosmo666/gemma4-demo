# Bank Statement Analyzer — Design Spec

**Date:** 2026-04-10
**Owner:** Prerak Gupta
**Status:** Draft v1 — approved for implementation planning
**Primary goal:** A local, single-user, multimodal tool that ingests SBI and HDFC bank statement PDFs (in any mix of yearly / quarterly / monthly slices), extracts transactions, categorizes them, and answers ten specific expense-analysis questions via four dashboards.

---

## 1. Motivation

Bank portals and existing apps (Moneycontrol, INDMoney, Walnut) all fail at the same thing: they show *what* you spent but not *what it actually means*. The "monthly expense" number they show is polluted by transfers to your own accounts, investment debits (SIPs, RDs), and one-off big items (annual insurance premium, a laptop purchase) that make the monthly burn look wildly different than it really is. There's no way to answer questions like "what do I actually consume in a typical month, excluding the weird stuff?"

This project is a personal tool that treats raw bank statements as the source of truth, extracts every transaction with a multimodal LLM, and surfaces the answers to the specific questions the owner actually cares about. Everything runs locally — no cloud, no APIs, no third party ever sees an account number.

## 2. Scope

### 2.1 In scope (v1)

**Sources:**

- SBI bank statement PDFs
- HDFC bank statement PDFs
- Any mix of period slices: yearly, quarterly, monthly, or single-month archives
- Any order of upload (later uploads can cover older periods; re-uploads are no-ops)

**Four dashboards answering ten questions:**

| Dashboard | Questions answered |
|---|---|
| **1. Monthly Overview** | Q1 real monthly burn (excluding transfers/investments/one-offs) · Q2 breakdown by category · Q8 income vs expense net position |
| **2. Recurring vs One-Time** | Q3 recurring vs one-time split · Q5 top 10 biggest expenses this month |
| **3. Trends & Leaks** | Q4 category month-over-month trend · Q6 how much on a specific merchant · Q9 small-frequent-spend leaks · Q10 diff view vs last month |
| **4. Anomalies** | Q7 what's unusual this month compared to typical |

All four dashboards are shipped together in v1. They share one filter bar (date range + account selector).

### 2.2 Out of scope (v1)

- Any bank other than SBI and HDFC
- Credit card statements (separate format; deferred to v2 if needed)
- Budgets and budget-vs-actual tracking
- Bill reminders / recurring expense alerts
- Multi-user support (ever)
- Mobile / responsive UI
- Cloud sync or backup
- Tax-related features (ITR, capital gains, TDS)
- Income-side analysis beyond total income figure
- Goal setting / saving targets
- Investment tracking (that's a different project)
- Automatic bank integration / account aggregation APIs
- LoRA fine-tuning (deferred to v2 only if a specific pain point emerges)

## 3. Owner profile

Stored as single-row config, used for display only in v1 (no adequacy checks or income-based rules yet).

| Field | Value |
|---|---|
| Age | 26 |
| Dependents | 0 |
| Annual income | ₹6,00,000 |
| Banks | SBI, HDFC |

## 4. Architecture

### 4.1 Pipeline

```
  ~/statements-inbox/  (watched folder; user drops PDFs here)
            │
            ▼
  ┌────────────────────┐
  │ File-hash check    │  SHA256 of file bytes → skip if already ingested
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Classify           │  Gemma 4 E4B vision: SBI or HDFC? period covered?
  └─────────┬──────────┘    (rejects non-statement files to misc/)
            ▼
  ┌────────────────────┐
  │ Extract header     │  Account number, statement period, opening/closing
  └─────────┬──────────┘    balance
            ▼
  ┌────────────────────┐
  │ Extract            │  Per page: render to image, Gemma 4 E4B extracts
  │ transactions       │  rows → pydantic schema → validation + retry
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Normalize +        │  Taxonomy lookup → override cache → few-shot LLM
  │ categorize         │    fallback. Detect merchant canonical name.
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Dedupe + insert    │  INSERT OR IGNORE on dedup_key → SQLite
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Review queue (UI)  │  Owner sees extracted + categorized rows;
  │                    │    approves / edits / rejects per document
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Dashboards         │  Four views, all backed by pandas queries over
  │ + ad-hoc chat      │    SQLite; text-to-SQL for free-form questions
  └─────────┬──────────┘
            ▼
       Localhost web UI  (http://127.0.0.1:8765)
```

### 4.2 Core principles

- **LLM never writes to the ledger.** It proposes extractions and categorizations; deterministic code validates and writes.
- **Idempotent ingestion.** Re-uploading the same file or overlapping period is a no-op. `INSERT OR IGNORE` on a deterministic dedup key guarantees this at the database layer.
- **Review queue by default.** Every ingested document lands in a pending state. Owner must approve before rows count toward dashboards. Can be disabled per-bank once trusted.
- **Categorization is layered.** Deterministic taxonomy lookup → user override cache → few-shot LLM fallback. Each layer is transparent and correctable.
- **Background processing with live progress.** Uploading 24 PDFs is a ~10-minute job. UI shows per-file status, owner can start reviewing as results come in.
- **Append-only audit log.** Every classification, extraction, edit, and override is written as JSONL for replay and debugging.
- **Offline-first.** No outbound network calls at all. All inference runs locally via Ollama.
- **Money as integers.** All amounts stored as signed integer paise (₹1 = 100). No floats anywhere in the financial pipeline.

### 4.3 Module layout

```
gemma4-demo/
├── app/
│   ├── ingest/
│   │   ├── watcher.py            # asyncio folder watcher
│   │   ├── pipeline.py           # orchestrates per-file flow
│   │   ├── classify.py           # Gemma call: doc → bank + period
│   │   └── extractors/
│   │       ├── sbi.py            # SBI-specific extraction prompt + schema
│   │       └── hdfc.py           # HDFC-specific extraction prompt + schema
│   ├── categorize/
│   │   ├── taxonomy.py           # static lookup table (merchant → category)
│   │   ├── overrides.py          # user-override cache
│   │   ├── few_shot.py           # prompt + in-context examples
│   │   └── merchant.py           # canonical merchant name resolution
│   ├── ledger/
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── upsert.py             # idempotent writes with dedup_key
│   │   ├── coverage.py           # per-account period coverage map
│   │   └── migrations/
│   ├── analytics/
│   │   ├── monthly.py            # dashboard 1 calculations
│   │   ├── recurring.py          # dashboard 2 calculations
│   │   ├── trends.py             # dashboard 3 calculations
│   │   └── anomalies.py          # dashboard 4 calculations
│   ├── llm/
│   │   ├── client.py             # Ollama HTTP wrapper
│   │   ├── prompts/              # one .md file per task
│   │   └── schemas.py            # pydantic response schemas
│   ├── web/
│   │   ├── server.py             # FastAPI app
│   │   ├── routes/
│   │   │   ├── upload.py
│   │   │   ├── review.py
│   │   │   ├── dashboards.py
│   │   │   ├── documents.py      # coverage map, re-process action
│   │   │   ├── chat.py           # free-form text-to-SQL
│   │   │   └── config.py
│   │   ├── templates/            # Jinja2 + htmx
│   │   └── static/               # CSS + Chart.js
│   └── audit/
│       └── log.py                # append-only JSONL
├── data/
│   ├── ledger.db                 # SQLite
│   └── audit/                    # JSONL logs
├── statements-inbox/             # user drops PDFs here
├── docs/superpowers/specs/
├── tests/
│   ├── fixtures/                 # synthetic statements
│   └── unit/
├── pyproject.toml
└── README.md
```

### 4.4 Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for PDF, pydantic, SQLAlchemy, pandas |
| LLM runtime | Ollama running `gemma4:e4b` | Multimodal, 128K context, function calling, 2.5 GB Q4. Zero-setup compared to HF/vLLM. |
| KV cache compression | Ollama native `OLLAMA_KV_CACHE_TYPE=q8_0` (optional) | TurboQuant defers to v2; Ollama's native quant gives half the benefit with no setup. |
| PDF parsing | pdf2image → Gemma vision (primary) · pdfplumber (text fallback for debugging) | Vision-first avoids per-bank layout templates |
| DB | SQLite via SQLAlchemy | Zero-ops, fits single-user, structured queries |
| Web | FastAPI + Jinja2 + htmx + Chart.js | No build step; live progress via htmx polling/SSE |
| Background jobs | asyncio tasks in-process | Single process, single user — no Celery/Redis |
| Auth | None | Bound to 127.0.0.1, single user |
| Packaging | uv | Fast, lockfile, modern |

## 5. Data model

### 5.1 `accounts`
One row per bank account the owner has.

- `id` (PK)
- `bank` — enum: `sbi` · `hdfc`
- `account_number_masked` — last 4 digits only
- `holder_name`
- `created_at`

### 5.2 `documents`
Every PDF that enters the inbox.

- `id` (PK)
- `path` — absolute path in inbox
- `file_sha256` — file-level dedup (skip re-parsing identical files)
- `bank` — inferred at classification time
- `account_id` — FK, resolved after header extraction
- `period_start`, `period_end` — what the statement claims to cover
- `status` — enum: `pending` · `classifying` · `extracting` · `reconciling` · `ready_for_review` · `approved` · `rejected` · `failed`
- `status_detail` — progress text or error message
- `txn_count_extracted`, `txn_count_new`, `txn_count_duplicate`
- `classified_at`, `extracted_at`, `approved_at`

### 5.3 `transactions`
The core table. One row per unique transaction.

- `id` (PK)
- `account_id` — FK
- `date` — ISO date
- `amount_paise` — signed integer (positive = credit, negative = debit)
- `description_raw` — exactly as extracted from statement
- `description_normalized` — lowercased, whitespace-collapsed, ref numbers stripped
- `merchant_canonical` — resolved merchant, nullable if unknown
- `category` — enum (see §6.1)
- `category_source` — enum: `taxonomy` · `override` · `llm` · `manual`
- `is_recurring` — bool, computed after ingestion
- `is_essential` — bool, derived from category
- `balance_after_paise` — nullable
- `source_document_id` — FK
- `dedup_key` — `sha256(account_id | date | amount_paise | description_normalized | within_day_counter)` — **UNIQUE constraint**
- `within_day_counter` — int, distinguishes legitimate same-day duplicates
- `created_at`

### 5.4 `category_overrides`
Owner corrections. Lookup happens before LLM categorization.

- `id` (PK)
- `match_kind` — enum: `exact_description` · `merchant` · `regex`
- `pattern`
- `category` — target category
- `created_at`

### 5.5 `merchant_canonical`
Cache of canonical merchant names for fuzzy matches.

- `id` (PK)
- `raw_description_pattern`
- `canonical_name` — e.g. `Swiggy`
- `category_hint` — optional, used if taxonomy lookup misses
- `created_at`

### 5.6 `recurring_series`
Detected recurring transactions (SIPs, EMIs, rent, subscriptions).

- `id` (PK)
- `account_id` — FK
- `merchant_canonical`
- `category`
- `cadence` — enum: `monthly` · `quarterly` · `yearly` · `weekly` · `irregular`
- `typical_amount_paise`
- `typical_day_of_month`
- `first_seen`, `last_seen`
- `confidence` — float 0..1
- `active` — bool; false if not seen in >90 days

### 5.7 `config`
Single-row owner profile.

- `age`, `dob`, `dependents`, `annual_income_paise`
- `one_off_threshold_paise` — default ₹10,000; amounts above this are flagged as candidate one-offs
- `leak_merchant_count_threshold` — default 4 (≥4 occurrences in a month = candidate leak)
- `leak_merchant_amount_threshold_paise` — default ₹50,000 (avg < this = small-frequent-leak)
- `anomaly_multiplier` — default 2.0 (>2× rolling median = anomaly)
- `updated_at`

### 5.8 `audit_log`
Append-only. Also mirrored to JSONL on disk.

- `id`, `ts`, `event_type`, `entity`, `entity_id`, `payload` JSON

## 6. Categorization system

### 6.1 Category taxonomy (fixed set for v1)

```yaml
essential:
  - rent
  - utilities            # electricity, water, gas, internet, mobile
  - groceries
  - food_delivery
  - transport            # Uber, Ola, Metro, fuel
  - insurance_premium
  - healthcare
  - emi                  # loan repayments
  - subscriptions        # streaming, saas, newspapers

discretionary:
  - shopping
  - dining_out
  - entertainment
  - travel
  - personal_care
  - gifts_donations
  - misc_discretionary

not_expense:
  - income_salary
  - income_other
  - transfer_own         # between your own accounts
  - investment_sip       # SIPs, RDs, ELSS
  - investment_other     # direct stocks, MF purchases from bank
  - refund
  - loan_received
  - cash_withdrawal      # ATM — counted separately, see §6.4
```

Each category has two flags computed in code (not stored):
- **is_expense** — true for `essential` and `discretionary`
- **is_essential** — true for `essential` only

### 6.2 Three-layer categorization

For each transaction during ingestion, try in order:

1. **Taxonomy lookup** — deterministic match on description or merchant against a static YAML file (`app/categorize/taxonomy.yaml`). Covers ~70% of common Indian merchants.
2. **Override cache** — check `category_overrides` table. Covers user corrections from prior sessions.
3. **Few-shot LLM** — send batch of 20 uncategorized descriptions to Gemma 4 E4B with ~15 in-context examples drawn from the owner's prior corrections. Enforce schema via pydantic.

`category_source` field records which layer made the decision, so the UI can show confidence.

### 6.3 Canonical merchant resolution

Runs in parallel with categorization:

1. Lookup `merchant_canonical` table by `raw_description_pattern`
2. If miss: send to LLM with prompt "extract canonical merchant name" + examples
3. Cache the result for next time

Over time (1–2 months of use), cache hit rate approaches 95%.

### 6.4 Special handling

- **ATM withdrawals** are tagged `cash_withdrawal`. They are *not* counted in the monthly burn (because we don't know what the cash was spent on) but are shown separately on the Monthly Overview dashboard as "Cash withdrawn."
- **Self-transfers** (e.g., SBI → HDFC) are detected by matching credit and debit pairs across accounts within 2 days. Tagged `transfer_own`, excluded from burn.
- **Reversed transactions** (debit + matching credit same day, same description) are cancelled out at read time, not deleted.

## 7. Dedup design

### 7.1 Dedup key formula

```
dedup_key = sha256(
    account_id || '|' ||
    date (ISO) || '|' ||
    amount_paise (signed int as string) || '|' ||
    description_normalized || '|' ||
    within_day_counter (int)
)
```

`within_day_counter` starts at 0 and increments within each source document for any (date, amount, description) tuple that repeats inside that document. This handles legitimate duplicates like two separate ₹150 chai shop UPI payments on the same day — each source document that contains both will agree on the counter (0, then 1).

### 7.2 Ingestion decision flow

For each extracted transaction:

1. Compute `dedup_key`
2. `INSERT OR IGNORE INTO transactions ...`
3. If inserted: `txn_count_new++`
4. If ignored: `txn_count_duplicate++`

### 7.3 File-level dedup

Before parsing a file at all:

1. Compute `file_sha256` of the bytes
2. If a `documents` row with the same hash exists: skip parsing entirely; log "already processed"
3. Otherwise proceed with classification

This saves minutes per re-upload and ensures zero wasted LLM calls.

### 7.4 Coverage map

The Documents tab renders a per-account timeline showing which months are covered by at least one approved document. Gaps are highlighted. Dashboards flag months that are not fully covered so the owner doesn't misread a data hole as low spending.

## 8. LLM interface

All LLM calls go through `app.llm.client`. Every call has:

- A named prompt template (versioned as a file in `app/llm/prompts/`)
- A pydantic response schema
- Retry on schema failure (max 3)
- Full request/response logged to audit log
- Model-agnostic interface (swap `gemma4:e4b` → anything Ollama serves by flipping one config value)

### 8.1 LLM tasks

| Task | Input | Output schema |
|---|---|---|
| Classify document | First-page image | `{bank, period_start, period_end, confidence, reason}` |
| Extract header | Full first-page image + text | `{account_number_masked, holder_name, period_start, period_end, opening_balance_paise, closing_balance_paise}` |
| Extract transactions (per page) | Page image | `[{date, amount_paise, description_raw, balance_after_paise?}, ...]` |
| Categorize batch | 20 descriptions + 15 few-shot examples | `[{index, category, confidence, reason?}, ...]` |
| Canonical merchant (batch) | Raw descriptions | `[{index, canonical_name}, ...]` |
| Text-to-SQL (chat) | English question + full schema | `{sql, explanation, safety_check: "select_only"}` |

### 8.2 What the LLM never does

- Compute any sum, difference, average, percentage, or trend (deterministic code only)
- Decide whether a transaction is recurring (deterministic algorithm, §9.2)
- Decide what is an anomaly (deterministic algorithm, §9.4)
- Write to the ledger directly
- Execute SQL (we parse, validate read-only, then execute in code)

### 8.3 Text-to-SQL safety

The chat interface lets the owner ask free-form questions. Safety rails:

1. LLM is prompted to emit SELECT-only SQL
2. Generated SQL is parsed by `sqlglot`; any non-SELECT statement is rejected
3. Allowed table list is restricted (no reads from `audit_log` or `config`)
4. Query runs in a read-only SQLite connection
5. Results rendered as a table; owner sees the SQL that ran

## 9. Dashboards

All four run pure pandas queries on the SQLite ledger. No LLM at dashboard render time (unless owner uses the chat tab).

### 9.1 Dashboard 1 — Monthly Overview

**Inputs:** account filter · date range (default current month)

**Computations:**

```
income = SUM(amount_paise) WHERE amount > 0 AND category IN (income_*)
expense_all = -SUM(amount_paise) WHERE amount < 0 AND category IN (is_expense categories)
one_offs = expenses WHERE amount > config.one_off_threshold_paise AND NOT is_recurring
real_burn = expense_all - one_offs
cash_withdrawn = -SUM(amount_paise) WHERE category = 'cash_withdrawal'
```

**Renders:**

- Big number: `real_burn` (₹X lakhs)
- Secondary: `income`, `expense_all`, `one_offs`, `cash_withdrawn`
- Net position: `income - expense_all`
- Pie chart: category breakdown of `expense_all`
- "One-offs this month" list (clickable → see the transactions)
- Coverage warning if date range spans uncovered months

### 9.2 Dashboard 2 — Recurring vs One-Time

**Recurring detection** (deterministic algorithm, run after every ingest):

1. Group transactions by `(account_id, merchant_canonical)` with at least 3 rows in the last 180 days
2. For each group, check if the gaps between transaction dates form a consistent cadence:
   - Monthly: median gap ∈ [25, 35] days, stddev < 5
   - Quarterly: median gap ∈ [85, 95] days
   - Weekly: median gap ∈ [6, 8] days
   - Yearly: median gap ∈ [355, 375] days
3. Check amount consistency: stddev of amounts / mean amount < 0.1 (10% tolerance)
4. If both checks pass: create/update a `recurring_series` row, mark member transactions `is_recurring = true`

**Dashboard shows:**

- Two columns: "Every month" (recurring, currently active) and "One-time this month"
- Recurring column: merchant · amount · cadence · next expected date · first seen · active/inactive
- One-time column: top 10 by amount
- Sum at the bottom of each column

### 9.3 Dashboard 3 — Trends & Leaks

**Category trends:**

- For each date in the filter range, group transactions by `(month, category)` and sum
- Render as stacked area + line chart (Chart.js)
- Owner can click a category to drill into its transactions

**Diff vs last month:**

- Compute category totals for current month and previous month
- Sort by absolute diff
- Render as a waterfall-style bar chart + table

**Merchant search:**

- Input box; type "Swiggy" → live filter of transactions where `merchant_canonical ILIKE '%swiggy%' OR description_normalized ILIKE '%swiggy%'`
- Show total, count, average per transaction, monthly timeline

**Leaks:**

- Group by `(month, merchant_canonical)`
- Filter to groups where count ≥ `config.leak_merchant_count_threshold` AND average amount < `config.leak_merchant_amount_threshold_paise`
- Sort by total × frequency
- Render as a table: merchant · occurrences · avg · total · monthly trend sparkline

### 9.4 Dashboard 4 — Anomalies

**Algorithm:**

1. For each category, compute rolling 3-month median and MAD (median absolute deviation)
2. Current month total > median + `config.anomaly_multiplier` × MAD → flag as anomaly
3. Also compute per-merchant: any merchant with >2× average monthly spend is flagged

**Dashboard shows:**

- List of anomalous categories: "Food delivery up 180% vs typical"
- List of anomalous merchants
- Drill-in: click an anomaly to see the specific transactions driving it
- Edge case: if fewer than 3 full prior months exist, show "insufficient history" instead of computing noise

## 10. User experience

### 10.1 Single-page localhost app at `http://127.0.0.1:8765`

**Top nav:** Dashboards · Review Queue (with badge) · Documents · Chat · Config

**Default landing:** Dashboards with the 4 views as tabs or stacked sections. One shared filter bar.

### 10.2 Upload & review flow

1. Owner drops PDFs into `statements-inbox/` (or uses the upload widget)
2. Watcher picks up new files, adds `documents` rows with status `pending`
3. Background worker processes one file at a time:
   - `classifying` → `extracting` (with page counter) → `reconciling` → `ready_for_review`
4. Review queue badge increments; owner can open the queue at any time
5. Per-document review screen shows:
   - Inferred bank, account, period
   - Extracted transactions table with editable categories
   - Counts: extracted / new / duplicate
   - Approve · Edit · Reject buttons
6. On approve: rows counted toward dashboards, audit log entry written
7. On reject: document status set to `rejected`, no rows counted, audit log entry

### 10.3 Documents tab

- Coverage map per account
- Full list of processed documents with status, period, counts
- Re-process action (forces re-extraction)
- Delete action (removes document and its transactions, logged)

### 10.4 Chat tab

- Single text input
- Owner types a question
- Backend: text-to-SQL via Gemma → sqlglot safety parse → execute → render result
- Show the generated SQL below the result (transparency)
- Save chat history locally for reference

### 10.5 Config tab

- Edit owner profile
- Edit thresholds (one-off, leak, anomaly multiplier)
- View / edit category overrides (rules table)
- View / edit merchant canonical cache

## 11. Failure modes and safety rails

| Failure | Mitigation |
|---|---|
| LLM returns invalid JSON | pydantic retry (max 3), then mark document failed with error in status_detail |
| LLM hallucinates a transaction | Review queue shows every row before ledger write; owner catches obvious errors |
| Duplicate from overlapping periods | UNIQUE constraint on dedup_key; INSERT OR IGNORE |
| Same file uploaded twice | file_sha256 check skips re-parsing entirely |
| Password-protected PDF | Per-document password prompt in UI; passwords optionally cached per-bank in config |
| Non-statement file | Classifier returns `unknown`; document moved to `misc/` subfolder, logged |
| Categorization wrong | Edit in review queue, creates an override for future transactions |
| Recurring detection wrong | Manual toggle `is_recurring` in the transaction edit view |
| Anomaly false positive | Owner can dismiss; dismissed items stored so they don't re-surface |
| Text-to-SQL generates dangerous SQL | sqlglot validation rejects anything non-SELECT; read-only connection |
| Corrected transaction from bank | Review queue flags new transactions suspiciously close to existing ones (same date, ±1% amount, similar description); owner confirms or rejects |
| Missing month in data | Dashboards flag "incomplete data for this period" in the coverage bar |

## 12. Security and privacy

- **Bound to 127.0.0.1 only.** Never exposed to the network.
- **No outbound network calls.** Period. All inference local via Ollama.
- **Account numbers masked** in logs (last 4 only). Raw PDFs stay in the inbox folder; nothing copied unless owner moves it.
- **No telemetry.** No crash reports, update pings, usage metrics.
- **Database file permissions.** `ledger.db` mode `0600` on Unix; owner-only ACL on Windows.
- **Audit log is owner-readable.** JSONL files in `data/audit/` with hash-chain for tamper evidence.
- **Passwords for PDFs** optionally stored in OS keychain (Windows Credential Manager); fallback is per-document prompt never written to disk.

## 13. Testing

- **Unit tests** for all deterministic code: dedup key computation, recurring detection, anomaly detection, XIRR not applicable here, leak detection, category derivation.
- **Fixture tests** for extractors: synthetic SBI and HDFC statement images with known expected rows. Real statements kept gitignored; synthetic subset committed.
- **Dedup invariant tests**: ingest the same transactions via (a) yearly, (b) quarterly, (c) monthly source documents in varying orders — assert final row count is always identical.
- **Contract tests** for LLM client: mock Ollama responses, verify schema enforcement and retry behavior.
- **End-to-end smoke test**: drop a synthetic yearly PDF → approve → verify all 4 dashboards render without errors and key numbers match expected fixtures.
- **No LLM-dependent tests in CI.** Those run locally with `RUN_LLM_TESTS=1`.

## 14. Milestones (high level; refined in the implementation plan)

1. **Foundations** — project scaffold, SQLAlchemy models, migrations, Ollama client wrapper, pydantic schemas, audit log, taxonomy YAML
2. **Ingestion vertical slice** — single-PDF happy path: classify → extract header → extract transactions → dedupe → insert. Raw transactions visible in a debug page. Covers SBI first.
3. **Categorization pipeline** — three-layer system (taxonomy → override → LLM), canonical merchant resolution, manual edit in review queue
4. **Dashboard 1: Monthly Overview** — pandas calculations + UI, including one-off exclusion logic and coverage warnings
5. **HDFC extractor** — second bank support; verify dedup across accounts
6. **Recurring detection + Dashboard 2** — detection algorithm, Recurring vs One-Time view
7. **Dashboard 3: Trends & Leaks** — category trends, diff view, merchant search, leak detection
8. **Dashboard 4: Anomalies** — rolling median/MAD, per-category and per-merchant flags
9. **Chat tab (text-to-SQL)** — sqlglot safety, read-only connection, UI
10. **Polish** — coverage map UI, review queue ergonomics, documents tab, config tab, end-to-end smoke test

## 15. UX and visual design

Design decisions below are grounded in the `ui-ux-pro-max` skill output (persisted under `design-system/expense-lens/MASTER.md`). The picked pattern is **Real-Time / Operations Landing** and the style is **Data-Dense Dashboard** — both chosen because this tool is a personal analytics surface where data visibility matters more than whitespace or brand flourish.

### 15.1 Design tokens

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `#2563EB` | Interactive elements, active nav, primary buttons |
| `--color-primary-600` | `#1D4ED8` | Pressed / hover of primary |
| `--color-accent` | `#F97316` | Single primary CTA per screen (e.g., "Approve & Ingest") |
| `--color-bg` | `#F8FAFC` | App background |
| `--color-surface` | `#FFFFFF` | Cards, panels |
| `--color-border` | `#E2E8F0` | Subtle dividers |
| `--color-text` | `#1E293B` | Primary text (contrast 15.3:1 on bg — AAA) |
| `--color-text-muted` | `#64748B` | Secondary text (contrast 5.0:1 on bg — AA) |
| `--color-success` | `#16A34A` | Positive income, approved state |
| `--color-warning` | `#F59E0B` | Anomaly moderate, review pending |
| `--color-danger` | `#DC2626` | Anomaly severe, rejected, destructive |
| `--color-neutral-grid` | `#E2E8F0` | Chart gridlines (low-contrast, doesn't compete with data) |
| `--radius-sm` | `4px` | Inputs, chips |
| `--radius-md` | `8px` | Cards, buttons |
| `--space-1` | `4px` | Base unit for 4pt spacing scale |
| `--space-2` | `8px` | Row gaps, small paddings |
| `--space-3` | `12px` | Field padding |
| `--space-4` | `16px` | Card padding, section gaps |
| `--space-6` | `24px` | Dashboard card gaps |
| `--space-8` | `32px` | Section separators |
| `--shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` | Card elevation |
| `--shadow-md` | `0 4px 6px rgb(0 0 0 / 0.07)` | Modals, popovers |
| `--duration-fast` | `150ms` | Micro-interactions |
| `--duration-normal` | `200ms` | State changes |
| `--ease-out` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Enter animations |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exit animations |

All colors define light mode only for v1. Dark mode deferred to v2 (requires independent contrast verification per design system rules).

### 15.2 Typography

- **Body / UI:** `Fira Sans` (300/400/500/600/700) — clean, data-friendly, pairs with the dashboard style
- **Tabular numerals:** `Fira Code` (400/500) — monospaced, used *only* for currency amounts and numeric table columns so row totals stay perfectly aligned (see rule `number-tabular`)
- **Base size:** 16px (required for mobile to avoid iOS auto-zoom)
- **Scale:** 12 · 14 · 16 · 18 · 24 · 32 · 48
- **Line height:** 1.5 for body, 1.2 for headings
- **Font loading:** `font-display: swap`, preload only Fira Sans 400 + 600
- **Self-hosted** under `app/web/static/fonts/` — no outbound calls (reinforces the offline-first principle in §4.2)

### 15.3 Layout shell

- **Responsive breakpoints:** 375 / 768 / 1024 / 1440 (v1 optimizes for desktop 1280+ but must not break on 375)
- **Max content width:** 1440px, centered with 24px gutters
- **Persistent layout:**
  - Top app bar (64px): app name, filter bar trigger, review queue badge, chat icon, config icon
  - Sidebar (240px, collapsible to 64px): nav items — Dashboards · Review Queue · Documents · Chat · Config · (bottom) Account picker
  - Main area: scroll region with reserved top/bottom padding so sticky elements never overlap
- **Filter bar:** sticky secondary row below the top bar, always visible on Dashboards; date range picker + account multi-select (SBI / HDFC / Both) — changes fan out to all four dashboards via one shared query state

### 15.4 Dashboard layouts

#### Dashboard 1 — Monthly Overview

A 12-column grid, 24px gaps:

- **Row 1** (hero KPIs, 4 cards × 3 cols each):
  - **Real monthly burn** — large Fira Code number, delta chip vs prior month (color: success if lower, danger if higher), subtitle "excluding transfers, investments, and one-offs"
  - **Total spend** — gross number + count of transactions
  - **One-offs excluded** — amount + "X items" link that opens a modal
  - **Net position** — income − expense, color-coded
- **Row 2** (pie + bar, 6 cols each):
  - **Category breakdown** — horizontal bar chart (NOT pie — essential categories can easily exceed 5, and the skill rule `no-pie-overuse` forbids pie beyond 5 slices). Each bar labeled directly with amount (rule `direct-labeling`).
  - **Income vs expense** — stacked column or bullet chart; bullet wins because the skill rates it AAA accessibility (rule: `Result 4` of chart search)
- **Row 3** (12 cols): recent transactions table, sortable, sticky header, virtualized if >50 rows

Coverage warnings appear as a yellow `--color-warning` strip at the top of the dashboard if the filter range includes any month with incomplete data.

#### Dashboard 2 — Recurring vs One-Time

- **Two equal columns, 6 cols each:**
  - **Recurring** (left): table — merchant · cadence chip · typical amount · next expected date · first seen · active indicator. Sorted by typical_amount desc.
  - **One-time this month** (right): table — date · merchant · category · amount · source. Sorted by amount desc, limited to top 10 with "View all N" link.
- **Bottom strip:** two summary cards showing total recurring and total one-time

#### Dashboard 3 — Trends & Leaks

- **Row 1** — Category trend line chart (full width, 420px tall): multiple series with distinct line styles (solid / dashed / dotted) per rule `color-not-decorative-only`. Togglable legend, hover tooltip shows exact ₹ per category per month.
- **Row 2** (6 + 6 cols):
  - **Diff vs last month** (left): waterfall-style horizontal bar, sorted by absolute change, positive changes in danger, negative in success
  - **Merchant search** (right): input field at top; below it, a live-filtered card showing total, count, avg, and a sparkline timeline
- **Row 3** (full width): **Leaks panel** — sortable table with monthly sparkline per row

#### Dashboard 4 — Anomalies

Matches the skill's first chart recommendation exactly (Result 1: "Line Chart with Highlights" for anomaly detection).

- **Row 1** — per-category anomaly cards, one per flagged category: category name, "↑ 180% vs typical" chip, median line + current month marker in danger color, sparkline
- **Row 2** — per-merchant anomalies, same card pattern
- Each card is clickable to drill into the specific transactions driving the anomaly
- **Empty state:** "No anomalies this month — spending is within your typical range" + illustration
- **Insufficient history state:** "Need at least 3 months of data for anomaly detection. You currently have N months."

### 15.5 Review queue UX

The review queue is the most important interaction surface because it's where trust in the extraction is built.

- **List view:** one card per document in `ready_for_review` status
  - Card header: bank logo, inferred period, counts (N extracted · M new · K duplicate)
  - Card body: collapsed by default, expands inline to show all transactions
  - Actions: **Approve & Ingest** (primary CTA, accent orange), **Edit**, **Reject**
- **Live progress:** documents in `classifying` / `extracting` status show a skeleton card with a progress strip at the top. Per rule `loading-states`, anything > 300ms gets a skeleton, not a spinner.
- **Low-confidence markers:** any transaction where `category_source == 'llm'` and confidence is low gets a yellow left border and is pre-focused for review
- **Bulk edit:** multi-select transactions → change category for all at once. Any bulk edit creates an `override` rule (match on merchant) so the correction applies to future documents automatically.
- **Feedback loop:** every edit adds an entry to the few-shot example pool visible in Config → Categorization
- **Undo:** after approval, a toast appears with "Approved 142 transactions · Undo" for 5 seconds (rule `undo-support`)

### 15.6 Interaction and motion

- All buttons have visible focus rings (2px `--color-primary` outline with 2px offset)
- Hover transitions: 150ms ease-out on background / border
- Card press feedback: subtle scale to 0.98 on active
- Modal enter: fade + scale from 0.96, exit 60% duration
- Respects `prefers-reduced-motion`: all transitions drop to 0.01ms under that media query
- Loading states use skeleton shimmer, not spinners, for anything > 300ms
- Every form submission disables its button and shows inline progress

### 15.7 Accessibility guarantees

- Contrast: body text 15.3:1, muted text 5.0:1, all interactive primaries ≥ 4.5:1
- Every interactive element has a visible label or `aria-label` (no icon-only buttons)
- Keyboard navigation: Tab order matches visual order; Esc closes modals; `/` focuses search
- Charts have `aria-label` summary + a "View as table" toggle (rule `screen-reader-summary`, `data-table`)
- Anomaly indicators use shape + color, not color alone (red circle marker on the line chart)
- Required form fields marked with asterisk and `aria-required`
- Error messages appear inline under the field with `role="alert"`
- Touch targets ≥ 44×44px on any touch-capable device

### 15.8 Empty, loading, and error states (per screen)

| Screen | Empty | Loading | Error |
|---|---|---|---|
| Dashboards | "No data yet. Drop a bank statement PDF into the inbox to get started." + button to open upload modal | Skeleton cards with shimmer | "Couldn't load dashboard — retry" with retry button |
| Review queue | "Nothing to review. Drop PDFs in `statements-inbox/` to process them." | Per-document skeleton with progress strip | Per-document error card with reason + "Retry extraction" |
| Documents | "No documents yet." | Table skeleton | Error toast |
| Chat | Default quick-question chips ("What's my burn?", "Top 5 merchants?", "Swiggy total?") | Loading ellipsis in chat bubble | Red bubble with "SQL generation failed — try rephrasing" |
| Coverage map | "No accounts yet — upload a statement to start" | Bar skeleton | Error strip |

### 15.9 Anti-patterns (explicitly forbidden)

From the skill output plus project-specific rules:

- **No emoji as icons** — use Lucide / Heroicons SVG only
- **No pie chart for category breakdown** (> 5 categories expected)
- **No ornate / decorative design** — this is a data tool
- **No gradients on data bars** — obscures values (rule `trend-emphasis`)
- **No animating `width` / `height`** — `transform` only
- **No placeholder-only labels** — every input gets a visible label above it
- **No error messages without recovery path** — every error says what to do next
- **No color-only meaning** — anomaly markers combine color + shape + text
- **No tooltips as the only way to see a value** — direct labels on all small charts
- **No blocking spinners for operations under 300ms** — instant state changes in that window

## 16. Open questions deferred to implementation planning

- Exact Ollama multimodal API shape for `gemma4:e4b` — verify when implementation starts (vision input format: base64 vs file reference)
- Whether pdf2image + Poppler on Windows needs bundled binaries or relies on system install
- Whether to use htmx polling or SSE for live ingestion progress (both work; pick in implementation)
- Initial taxonomy YAML contents — derived from owner's first month of real transactions during implementation
- Few-shot example seed set — start empty, grow from owner corrections

These do not affect the architecture or data model.

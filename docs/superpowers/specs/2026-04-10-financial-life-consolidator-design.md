# Financial Life Consolidator — Design Spec

**Date:** 2026-04-10
**Owner:** Prerak Gupta
**Status:** Draft v1 — approved for implementation planning
**Primary goal:** A local, multimodal, agentic personal-finance tool that ingests messy Indian financial documents (PDFs, screenshots, CSVs), builds a unified ledger, and answers five specific questions about the owner's financial life.

---

## 1. Motivation

Existing personal-finance tools (Moneycontrol, INDMoney, Mint, Kuvera) are incomplete for an Indian user because they depend on API aggregators that miss significant slices of real portfolios: ULIPs, EPF, employer-linked insurance, offline FDs, crypto, old broker accounts. Coverage holes mean the "net worth" they show is always wrong.

This project takes the opposite approach: **ingest whatever the user can dump into a folder** — bank PDFs, broker exports, CAMS CAS, EPFO passbooks, insurance policy documents, crypto CSVs — and let a multimodal LLM do the heavy lifting of extraction and normalization. No bank integrations, no aggregator APIs, no accounts.

Two additional constraints shape the design:

- **Privacy is non-negotiable.** The data in question (PAN, account numbers, holdings, salary) cannot leave the machine. All inference runs on a local Gemma 4 model; network access is limited to public price/NAV endpoints.
- **This is a personal tool for one user.** Design decisions optimize for the owner's actual source list, not a generic Indian user.

## 2. Scope

### 2.1 In scope (v1)

**Document sources:**

| # | Source | Format | Role |
|---|---|---|---|
| 1 | SBI bank statement | PDF (password-protected) | Cash balance + monthly burn |
| 2 | HDFC bank statement | PDF (password-protected) | Cash balance + monthly burn |
| 3 | Zerodha Console exports | PDF + CSV (holdings, P&L, tradebook, ledger) | Equity holdings + transactions |
| 4 | Groww exports | PDF + CSV | Equity + MF holdings |
| 5 | CAMS CAS (detailed) | PDF (password-protected) | **Primary MF source** — holdings + full txn history |
| 6 | EPFO passbook | PDF | Retirement balance (if exists) |
| 7 | Edelweiss Flexi Life policy | PDF | ULIP: fund value + sum assured + premium |
| 8 | Tata AIG health policy | PDF | Coverage only |
| 9 | Plum (employer health) | PDF / screenshot | Coverage only (employer-conditional) |
| 10 | Binance export | CSV | Crypto holdings + transactions |

**Derived views (one dashboard per question):**

1. **Net worth today** — single headline number + breakdown by source
2. **True asset allocation (look-through)** — equity / debt / cash / gold / crypto based on underlying MF portfolio composition, not surface bucket labels
3. **XIRR leaderboard** — per-holding annualized return, ranked worst-to-best
4. **Insurance adequacy** — health and life coverage compared to rules of thumb for the owner's profile
5. **Emergency runway** — months of essential expenses covered by liquid assets

### 2.2 Out of scope (v1)

- Natural-language chat interface (stretch goal; v1 ships with fixed dashboards only)
- Alerts / notifications (FD maturity, renewal reminders) → v2
- Mobile / responsive UI → v2
- Multi-user support → never
- Cloud sync / backup → v2
- Tax reports, ITR prep → separate project
- Rebalancing suggestions → v2
- Goal tracking → v2
- Custom transaction categorization rules (v1 relies on LLM classification with manual override)
- Gold, physical alternatives, real estate, loans, foreign holdings, term life, other banks / brokers — owner does not have these

### 2.3 Known gaps to close before v1 can fully work

Neither is blocking the build; both block the end-to-end output being accurate.

1. **CAMS CAS re-subscription** — owner's monthly CAS stopped arriving one month ago. Without it, the MF pipeline is blind. Fix: re-subscribe (detailed, not summary) at camsonline.com.
2. **EPFO passbook check** — owner is unsure if EPF exists. Fix: pull UAN from any payslip, download passbook PDF from passbook.epfindia.gov.in. If no EPF exists, source #6 drops from v1.

## 3. Owner profile (config)

Used by the insurance adequacy and runway calculations. Stored in a single config file; first-run UI collects these if missing.

| Field | Value |
|---|---|
| Age | 26 |
| DOB | 2000-03-21 |
| Dependents | 0 |
| Annual income | ₹6,00,000 |
| Employment type | Salaried |

**Key implication:** with zero dependents, term life insurance is not a stated need. The adequacy check will report life insurance as "not required" rather than flagging a shortfall. This logic must re-evaluate automatically if `dependents > 0` in the future.

## 4. Architecture

### 4.1 High-level pipeline

```
  ~/finance-inbox/  (watched folder; user drops docs here)
            │
            ▼
  ┌────────────────────┐
  │ Ingest + Classify  │  Gemma 4 vision: "what document type is this?"
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Type-specific      │  Gemma 4 vision + pydantic schema per type:
  │ extractor          │   bank-statement, cams-cas, zerodha-pnl,
  │                    │   groww-holdings, ulip-policy, health-policy,
  │                    │   epfo-passbook, binance-csv
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Review queue (UI)  │  User sees extracted fields + confidence;
  │                    │  approves / edits BEFORE ledger write
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Normalize +        │  Gemma 4 text: resolve instrument names to
  │ reconcile          │  canonical IDs via local reference DB
  │                    │  (AMFI scheme codes, NSE/BSE ISINs)
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Ledger (SQLite)    │  instruments, holdings, transactions,
  │                    │  coverage, policies, snapshots, config
  └─────────┬──────────┘
            ▼
  ┌────────────────────┐
  │ Query + derive     │  5 fixed dashboards + pure-Python calcs
  │                    │  (XIRR, allocation roll-up, runway)
  └─────────┬──────────┘
            ▼
      Localhost web UI  (http://localhost:8765)
```

### 4.2 Core principles

- **The LLM never writes to the ledger directly.** It proposes extractions; deterministic code validates, the user reviews, and a separate upsert step commits.
- **Review queue by default.** Every new document lands in a pending state with extracted fields visible and confidence markers. Nothing reaches the ledger without explicit approval. The review gate can be disabled per doc-type later once trust is established.
- **Idempotent ingestion.** Re-processing the same document does not duplicate rows. Dedupe key varies by type (folio + txn date for MFs, ISIN + broker + trade date for equities, account + txn date + amount for bank).
- **Append-only audit log.** Every classification, extraction, approval, edit, and reconciliation event is written as a JSONL line with timestamp and source. Replay is possible from the log alone.
- **Offline-first.** All document processing is local. The only outbound network calls are:
  - AMFI NAV file (https://www.amfiindia.com/spages/NAVAll.txt) — daily
  - NSE/BSE bhavcopy — daily
  - Binance price API — on demand (only if the user opts in; cached)
- **Fail loud, not silent.** Any extraction the model is not confident about is flagged in the review queue with the reason. There is no "best guess and hope" path.

### 4.3 Module layout

```
gemma4-demo/
├── app/
│   ├── ingest/
│   │   ├── watcher.py           # asyncio folder watcher
│   │   ├── classify.py          # Gemma call: doc → type
│   │   └── extractors/
│   │       ├── bank_statement.py
│   │       ├── cams_cas.py
│   │       ├── zerodha.py
│   │       ├── groww.py
│   │       ├── ulip_policy.py
│   │       ├── health_policy.py
│   │       ├── epfo_passbook.py
│   │       └── binance_csv.py
│   ├── normalize/
│   │   ├── instruments.py       # scheme code / ISIN resolution
│   │   └── reference_db.py      # AMFI / NSE / BSE lookups
│   ├── ledger/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── upsert.py            # idempotent writes
│   │   └── migrations/
│   ├── derive/
│   │   ├── net_worth.py
│   │   ├── allocation.py        # look-through roll-up
│   │   ├── xirr.py
│   │   ├── insurance.py
│   │   └── runway.py
│   ├── prices/
│   │   ├── amfi.py              # NAV file download + cache
│   │   ├── nse.py
│   │   └── binance.py
│   ├── llm/
│   │   ├── client.py            # Ollama client wrapper
│   │   ├── prompts/             # one file per task
│   │   └── schemas.py           # pydantic response schemas
│   ├── web/
│   │   ├── server.py            # FastAPI app
│   │   ├── routes/
│   │   │   ├── review.py        # review queue UI + actions
│   │   │   ├── dashboards.py    # 5 dashboards
│   │   │   └── config.py
│   │   ├── templates/           # Jinja2 + htmx
│   │   └── static/
│   └── audit/
│       └── log.py               # append-only JSONL writer
├── data/
│   ├── ledger.db                # SQLite
│   ├── reference/               # AMFI NAVs, ISIN map
│   ├── cache/                   # prices, downloaded manifests
│   └── audit/                   # JSONL logs
├── finance-inbox/               # user drops docs here
├── docs/superpowers/specs/
├── tests/
├── pyproject.toml
└── README.md
```

### 4.4 Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for PDF parsing, pydantic, SQLAlchemy, scipy (XIRR) |
| LLM runtime | Ollama running Gemma 4 E4B locally | Easiest local multimodal serving; drop-in via HTTP |
| PDF parsing | pdfplumber (text) + pdf2image (render to image for vision) | Text fallback for layout-friendly PDFs, images for everything else |
| DB | SQLite via SQLAlchemy | Zero-ops, fits single-user, relationally rich |
| Web | FastAPI + Jinja2 + htmx + Chart.js | No build step, matches the "minimal JS" discipline from dpsecuregc; htmx for reactive review queue without a SPA |
| Job scheduling | asyncio background tasks | No Redis, no Celery — single process is enough |
| Auth | None | Localhost only, single user |
| Packaging | uv | Fast, lockfile, modern |

## 5. Data model

Thirteen core tables. Full DDL is deferred to implementation planning; this section locks the shape.

### 5.1 `documents`
Every file that enters the inbox becomes a row here, regardless of extraction outcome.

- `id`, `path`, `sha256`, `doc_type`, `status` (pending / extracted / approved / rejected / failed)
- `classified_at`, `extracted_at`, `approved_at`
- `source_metadata` JSON (filename, modification time, password used if any)

### 5.2 `extractions`
Raw LLM output for a document, independent of whether it's been approved.

- `id`, `document_id`, `schema_version`, `payload` JSON, `confidence_notes`
- `created_at`

### 5.3 `instruments`
Canonical registry of anything investable.

- `id`, `kind` (mf / equity / crypto / ulip_fund / epf / savings / fd / ppf / nps)
- `canonical_name`, `amfi_scheme_code`, `isin`, `symbol`, `ccy`
- Composition reference (FK to `portfolio_composition` if applicable)

### 5.4 `holdings`
Current state per instrument. One row per (instrument, account) pair.

- `id`, `instrument_id`, `account_id`, `units`, `avg_cost`, `as_of_date`, `source_document_id`

### 5.5 `transactions`
Full transaction history for any instrument. Required for XIRR.

- `id`, `instrument_id`, `account_id`, `kind` (buy / sell / dividend / switch_in / switch_out / interest / contribution)
- `date`, `units`, `amount`, `price`, `source_document_id`

### 5.6 `accounts`
Demat accounts, bank accounts, broker accounts, crypto exchanges, EPF UANs.

- `id`, `kind` (bank / demat / broker / crypto_exchange / epf / ppf)
- `institution`, `identifier_masked`

### 5.7 `bank_transactions`
Separate from investment transactions because they drive the runway calculation.

- `id`, `account_id`, `date`, `amount`, `description`, `category` (essential / discretionary / transfer / income), `llm_classified` bool
- `source_document_id`

### 5.8 `coverage`
Insurance protection (not net worth).

- `id`, `policy_id`, `kind` (health / life / motor / travel)
- `sum_insured`, `members_covered`, `premium_annual`, `renewal_date`
- `conditional` bool (true for employer policies), `conditional_note`

### 5.9 `policies`
Insurance policy metadata. A single policy can produce coverage + holdings + transactions (for ULIPs).

- `id`, `insurer`, `policy_number_masked`, `product_name`, `start_date`, `is_investment_linked`

### 5.10 `portfolio_composition`
AMFI-published monthly disclosures per MF scheme, used for look-through allocation.

- `id`, `amfi_scheme_code`, `as_of_date`
- `pct_equity`, `pct_debt`, `pct_cash`, `pct_gold`, `pct_other`
- Primary key (`amfi_scheme_code`, `as_of_date`)

### 5.11 `snapshots`
Daily point-in-time record for net worth history.

- `id`, `date`, `total_net_worth`, `breakdown` JSON

### 5.12 `config`
Single-row owner profile.

- `age`, `dob`, `dependents`, `annual_income`, `employment_type`, `runway_include_crypto` bool, `updated_at`

### 5.13 `audit_log`
Append-only JSONL on disk, mirrored to a table for easy querying. Schema is intentionally loose — `event_type`, `entity`, `entity_id`, `payload` JSON, `ts`.

## 6. LLM interfaces

All LLM calls go through a single client wrapper. Every call has:

- A named prompt template (versioned on disk)
- A pydantic response schema (retries on parse failure, max 3)
- Full request/response logging to the audit log
- A "why are you uncertain?" field the model is always allowed to populate

### 6.1 Tasks that use the LLM

| Task | Modality | Schema summary |
|---|---|---|
| Classify document | Vision (first page image) | `{doc_type: enum, confidence: enum[high/medium/low], reason: str}` |
| Extract bank statement | Vision + text | Header (bank, account, period) + list of transactions |
| Extract CAMS CAS | Vision + text | Per-folio: AMC, scheme, units, NAV, value + txn list |
| Extract Zerodha/Groww holdings | Vision + text | List of symbols/units/avg price |
| Extract ULIP policy | Vision + text | Fund value, sum assured, premium, renewal, fund names + composition references |
| Extract health policy | Vision + text | Sum insured, members, premium, renewal, conditional? |
| Extract EPFO passbook | Vision + text | Total balance, last contribution |
| Normalize instrument name | Text | Input name → best match from candidates (with score) |
| Classify bank transactions | Text (batched) | Per txn → category + confidence |

### 6.2 What the LLM explicitly does NOT do

- Write to the database
- Compute XIRR or any number (deterministic code only)
- Decide whether insurance is "adequate" (pure rule in code)
- Fetch prices (deterministic HTTP)
- Resolve file paths or run OS operations

This boundary is the safety rail. The LLM is a structured-output function, nothing more.

## 7. Query implementations

### 7.1 Q1 — Net worth today

Sum of:
- Bank balances (latest `as_of_date` per account)
- Equity holdings × current price (NSE bhavcopy)
- MF holdings × current NAV (AMFI)
- ULIP fund value (extracted from policy doc; stale-flagged if older than 30 days)
- EPF balance (extracted from passbook)
- Crypto holdings × current price (Binance API)

Output: headline number + table with one row per source, plus "as-of" timestamps per row. Snapshot written to `snapshots` daily.

### 7.2 Q2 — True asset allocation (look-through)

For each holding:

1. If `kind in (equity, crypto)`: counts 100% toward that asset class directly.
2. If `kind == mf` or `kind == ulip_fund`: look up latest `portfolio_composition` row for that scheme, multiply `units × NAV × pct_*` across equity / debt / cash / gold buckets.
3. If `kind in (bank_savings, fd, ppf, epf)`: counts 100% as cash or debt per a lookup table.

Output: stacked pie + table showing the difference between surface and look-through for transparency.

**Data dependency:** `portfolio_composition` must be pre-populated. Sourced from AMFI's monthly scheme portfolio disclosures (free, bulk download). If a scheme is missing, display the surface allocation and flag it. ULIP fund composition is manually ingested once from the insurer's fact sheet because AMFI doesn't cover ULIPs.

### 7.3 Q3 — XIRR per holding

For each instrument with a transaction history:

1. Build a cashflow list: outflows (buys, SIPs) negative, inflows (sells, dividends) positive.
2. Append a final positive cashflow equal to current value on today's date.
3. Solve for XIRR via `scipy.optimize.newton` (with `brentq` fallback if Newton fails to converge).
4. If the cashflow list has fewer than 2 flows or all same-sign, report "n/a — insufficient history."

Output: table sorted worst-first with columns: instrument, invested, current value, abs gain/loss, XIRR, first txn date.

### 7.4 Q4 — Insurance adequacy

**Health:**

- Total cover = sum of `coverage.sum_insured` where `kind=health`
- Total *unconditional* cover = same but excluding `conditional=true` rows
- Rule of thumb for single adult in metro: ≥ ₹10,00,000
- Output: "You have ₹X total health (₹Y unconditional after removing employer policy). Rule of thumb: ₹10L. You are [adequate / short by ₹Z / over-covered]."
- Always shows the caveat that employer cover vanishes on job change.

**Life:**

- If `config.dependents == 0`: output "Not required — no financial dependents. Your Edelweiss ULIP is categorized as investment, not protection."
- If `config.dependents > 0`: required ≈ 12 × annual income. Compare against sum of `coverage.sum_insured` where `kind=life`. Report gap.

### 7.5 Q5 — Emergency runway

**Liquid assets:**

- Bank balances (SBI + HDFC savings)
- Any holding with `instrument.kind in (bank_savings, liquid_mf, ultra_short_mf)` — identified by scheme category tag in AMFI metadata
- Crypto if `config.runway_include_crypto == true` (default: false)

**Monthly essential burn:**

- Take last 3 full calendar months of `bank_transactions`
- Filter to `category == essential`
- Group by month, take median
- Edge case: fewer than 3 months of data → use available months and flag low confidence

**Runway (months) = liquid_assets / monthly_essential_burn**

Output: big number + the two inputs that produced it + a list of the transactions that were classified as essential (so the owner can sanity-check and override).

## 8. User experience

### 8.1 Single-page localhost app at `http://localhost:8765`

Layout:

- **Top nav**: Dashboard · Review queue (with badge count) · Documents · Config
- **Default landing**: Dashboard with all 5 query cards
- **Review queue**: list of pending documents with inline expand-to-edit; approve / edit / reject buttons
- **Documents**: history of all ingested docs with status, extraction payload, re-process action
- **Config**: owner profile + runway settings

### 8.2 Review queue interaction

When a new document lands:

1. Classification runs → doc type + confidence shown
2. Extraction runs → structured fields rendered in a form, editable
3. Badge count increments
4. User opens the queue, reviews each extraction, edits any wrong fields, clicks "Approve & ingest"
5. On approval: normalize + reconcile + write to ledger + audit log entry
6. On reject: audit log entry, document status set to `rejected`, no ledger change

### 8.3 Dashboard refresh model

- Dashboards compute on load (query the ledger + current prices)
- Daily snapshot job runs at 23:00 local time to capture net worth history
- "Refresh prices now" button forces an AMFI / NSE / Binance pull

## 9. Failure modes and safety rails

| Failure | Mitigation |
|---|---|
| LLM returns invalid JSON | pydantic retry (max 3) with error fed back to model; after 3 failures, mark document failed and queue for manual extraction |
| LLM hallucinates a field | Review queue is the catch: user sees extracted values before ledger write |
| Wrong document type classification | User can override in review queue; triggers re-extraction with the correct extractor |
| Password-protected PDF | User supplies password once per institution, stored in OS keychain (stretch) or prompted per-doc (v1) |
| Duplicate ingestion | SHA256 of file checked at ingest; same hash → reuse prior extraction |
| Stale prices | Timestamp shown next to every price-dependent number; manual refresh button |
| Missing `portfolio_composition` | Fall back to surface allocation and flag the holding |
| XIRR non-convergence | brentq fallback; if still failing, report n/a with reason |
| Bank transaction miscategorization | User can re-label via the runway dashboard; override stored in a `txn_overrides` column and applied on re-compute |
| Inbox file that is not a financial document | Classifier returns `unknown`, document parked in a `misc` folder with a log entry |

## 10. Security and privacy

- **No outbound calls with document content.** Ever. Only public price/NAV endpoints, with no identifying parameters.
- **Sensitive data never logged in plaintext.** Account numbers and PANs are masked in audit logs (last 4 chars only).
- **No telemetry.** No crash reports, no usage metrics, no update pings.
- **Local file paths only.** The web UI is bound to `127.0.0.1`, not `0.0.0.0`.
- **Document storage.** Originals stay in `finance-inbox/`; nothing is copied to a processed/ folder unless the user moves it.
- **Database file permissions.** `ledger.db` created with mode `0600` on Unix; Windows ACL set to user-only.
- **Keychain (stretch).** PDF passwords stored in OS keychain when available, falling back to per-doc prompt.

## 11. Testing

- **Unit tests** for all deterministic code: XIRR, allocation roll-up, runway, insurance rules, upsert idempotency.
- **Fixture-based tests** for extractors: sample document → expected pydantic payload. Samples collected from the owner's real documents, stored under `tests/fixtures/` (gitignored for privacy; a synthetic subset committed for CI).
- **Contract tests** for the LLM client: mock Ollama responses, verify retry + schema enforcement.
- **End-to-end smoke test**: spin up the app, drop a synthetic CAS into inbox, approve, verify net worth changes.
- **No tests against the live LLM in CI.** LLM-dependent tests run only with `RUN_LLM_TESTS=1`.

## 12. Milestones (rough — firmed up in the implementation plan)

The plan document will break this down further. Ballpark:

1. **Foundations** — project scaffold, DB models, migrations, audit log, Ollama client wrapper, pydantic schemas
2. **First vertical slice** — CAMS CAS end-to-end: classify → extract → review → ledger → net worth dashboard. Proves the whole loop.
3. **Bank statements (SBI + HDFC)** — bank_transactions table, classification, runway dashboard
4. **Equity brokers (Zerodha + Groww)** — holdings + transactions, XIRR dashboard
5. **Look-through allocation** — AMFI portfolio composition ingestion + roll-up engine, allocation dashboard
6. **Insurance (Tata AIG + Plum + Edelweiss)** — coverage + policies + ULIP linkage, insurance dashboard
7. **EPF + Binance** — remaining instruments, final dashboard polish
8. **Review queue UX polish + daily snapshot job**

## 13. Open questions deferred to implementation planning

- Exact Ollama model ID and multimodal API shape for Gemma 4 (verify against HF page when implementation starts).
- Whether ULIP fund composition can be auto-extracted from the fact sheet or requires manual config entry.
- How AMFI portfolio composition is best ingested — direct XLSX parse vs PDF extraction.
- Password management UX for multi-bank PDFs (keychain vs per-doc prompt).
- Whether the review queue should auto-expire rejected docs or keep them visible in the Documents tab only.

These do not affect the architecture or data model and can be resolved inside the implementation plan.

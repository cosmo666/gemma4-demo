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

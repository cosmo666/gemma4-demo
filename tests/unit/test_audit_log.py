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

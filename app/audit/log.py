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

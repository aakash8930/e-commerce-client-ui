"""Observability: plain log file + JSONL audit trail of every action."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Logger:
    def __init__(self, log_dir: str | Path) -> None:
        self.dir = Path(log_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._log = logging.getLogger("jarvis")
        if not self._log.handlers:
            self._log.setLevel(logging.INFO)
            fh = logging.FileHandler(self.dir / "jarvis.log", encoding="utf-8")
            fh.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            )
            self._log.addHandler(fh)
        self.audit_path = self.dir / "audit.jsonl"

    def info(self, msg: str, **ctx: Any) -> None:
        self._log.info("%s %s", msg, ctx if ctx else "")

    def error(self, msg: str, **ctx: Any) -> None:
        self._log.error("%s %s", msg, ctx if ctx else "")

    def audit(self, event: str, **fields: Any) -> None:
        """Append one immutable audit record."""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": event,
            **fields,
        }
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

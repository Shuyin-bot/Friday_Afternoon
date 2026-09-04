"""Local persistence for raw and normalized email artifacts."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from .retriever import RetrievedEmail


class EmailArtifactStore:
    """Persist raw messages and JSON-safe normalized email representations."""

    def __init__(self, data_dir: str):
        """Create an artifact store rooted at `data_dir`."""
        self.root = Path(data_dir)
        self.raw_dir = self.root / "emails" / "raw"
        self.normalized_dir = self.root / "emails" / "normalized"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)

    def save(self, email: RetrievedEmail) -> tuple[Path, Path]:
        """Atomically save raw and normalized artifacts and return their paths."""
        stem = f"{self._safe_name(email.message_id or 'message')}-{email.uid}"
        raw_path = self.raw_dir / f"{stem}.eml"
        normalized_path = self.normalized_dir / f"{stem}.json"

        normalized = email.model_dump(exclude={"raw_message"})
        normalized["received_at"] = email.received_at.isoformat() if email.received_at else None
        for attachment in normalized["attachments"]:
            content = attachment.get("content")
            attachment["content"] = base64.b64encode(content).decode("ascii") if content else None

        self._atomic_write_bytes(raw_path, email.raw_message)
        self._atomic_write_text(normalized_path, json.dumps(normalized, indent=2, default=str))
        return raw_path, normalized_path

    @staticmethod
    def _safe_name(value: str) -> str:
        """Convert an email identifier into a filesystem-safe filename component."""
        return re.sub(r"[^A-Za-z0-9._-]", "_", value.strip("<>"))[:100]

    @staticmethod
    def _atomic_write_bytes(path: Path, content: bytes) -> None:
        """Write bytes through a temporary file before replacing the destination."""
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        """Write text through a temporary file before replacing the destination."""
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)

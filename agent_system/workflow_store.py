"""SQLite persistence for quotation workflow state and stage outputs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from .workflow_models import WorkflowStatus


class WorkflowStore:
    """Persist the latest state and payload for each mailbox email."""

    def __init__(self, database_path: str):
        """Open or create workflow state in `database_path`."""
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_state (
                    mailbox TEXT NOT NULL,
                    email_uid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (mailbox, email_uid)
                )
                """
            )

    def save(
        self,
        mailbox: str,
        email_uid: int,
        status: WorkflowStatus,
        payload: dict,
        error: str | None = None,
    ) -> None:
        """Save or replace the current workflow state for an email."""
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO workflow_state(mailbox, email_uid, status, payload, error, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mailbox, email_uid) DO UPDATE SET
                    status = excluded.status,
                    payload = excluded.payload,
                    error = excluded.error,
                    updated_at = excluded.updated_at
                """,
                (
                    mailbox,
                    email_uid,
                    status.value,
                    json.dumps(payload),
                    error,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def get(self, mailbox: str, email_uid: int) -> dict | None:
        """Return the latest workflow status and payload, if present."""
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM workflow_state WHERE mailbox = ? AND email_uid = ?",
                (mailbox, email_uid),
            ).fetchone()
        if row is None:
            return None
        return {
            "mailbox": row["mailbox"],
            "email_uid": row["email_uid"],
            "status": WorkflowStatus(row["status"]),
            "payload": json.loads(row["payload"]),
            "error": row["error"],
            "updated_at": datetime.fromisoformat(row["updated_at"]),
        }

    def close(self) -> None:
        """Close the SQLite connection."""
        with self._lock:
            self._connection.close()

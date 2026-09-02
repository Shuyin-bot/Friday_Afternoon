"""Durable SQLite state for IMAP cursors and email processing."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field

from .models import DetectedEmail


class EmailProcessingStatus(str, Enum):
    """Lifecycle states for an email as it moves through ingestion."""

    DETECTED = "DETECTED"
    RETRIEVED = "RETRIEVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailRecord(BaseModel):
    """Persisted state for one detected email."""

    model_config = ConfigDict(frozen=True)

    uid: int = Field(gt=0)
    mailbox: str = Field(min_length=1)
    status: EmailProcessingStatus
    error: str | None = None
    created_at: datetime
    processed_at: datetime | None = None


class EmailStateStore:
    """SQLite repository for mailbox cursors and idempotent email processing."""

    def __init__(self, database_path: str):
        """Open or create the state database at `database_path`."""
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS mailbox_state (
                    mailbox TEXT PRIMARY KEY,
                    last_queued_uid INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS email_messages (
                    mailbox TEXT NOT NULL,
                    uid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    processed_at TEXT,
                    PRIMARY KEY (mailbox, uid)
                )
                """
            )

    def get_last_queued_uid(self, mailbox: str) -> int:
        """Return the last UID confirmed as queued for `mailbox`."""
        with self._lock:
            row = self._connection.execute(
                "SELECT last_queued_uid FROM mailbox_state WHERE mailbox = ?",
                (mailbox,),
            ).fetchone()
        return 0 if row is None else int(row["last_queued_uid"])

    def record_detected(self, email: DetectedEmail) -> bool:
        """Record an email once and return whether this was its first observation."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection:
            result = self._connection.execute(
                """
                INSERT OR IGNORE INTO email_messages
                    (mailbox, uid, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email.mailbox, email.uid, EmailProcessingStatus.DETECTED.value, now),
            )
        return result.rowcount == 1

    def can_enqueue(self, email: DetectedEmail) -> bool:
        """Return whether an email is waiting to be queued or needs retrying."""
        with self._lock:
            row = self._connection.execute(
                "SELECT status FROM email_messages WHERE mailbox = ? AND uid = ?",
                (email.mailbox, email.uid),
            ).fetchone()
        return row is not None and row["status"] in {
            EmailProcessingStatus.DETECTED.value,
            EmailProcessingStatus.FAILED.value,
        }

    def mark_queued(self, email: DetectedEmail) -> None:
        """Mark an email queued and advance its mailbox cursor after queue insertion."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection:
            result = self._connection.execute(
                """
                UPDATE email_messages
                SET status = ?, error = NULL, processed_at = ?
                WHERE mailbox = ? AND uid = ? AND status IN (?, ?)
                """,
                (
                    EmailProcessingStatus.QUEUED.value,
                    now,
                    email.mailbox,
                    email.uid,
                    EmailProcessingStatus.DETECTED.value,
                    EmailProcessingStatus.FAILED.value,
                ),
            )
            if result.rowcount != 1:
                raise ValueError(f"Email {email.mailbox}:{email.uid} is not ready to be queued")
            self._connection.execute(
                """
                INSERT INTO mailbox_state(mailbox, last_queued_uid)
                VALUES (?, ?)
                ON CONFLICT(mailbox) DO UPDATE SET
                    last_queued_uid = MAX(last_queued_uid, excluded.last_queued_uid)
                """,
                (email.mailbox, email.uid),
            )

    def set_status(
        self,
        email: DetectedEmail,
        status: EmailProcessingStatus,
        error: str | None = None,
    ) -> None:
        """Set processing status and optionally store a failure message."""
        processed_at = datetime.now(timezone.utc).isoformat() if status == EmailProcessingStatus.COMPLETED else None
        with self._lock, self._connection:
            result = self._connection.execute(
                """
                UPDATE email_messages
                SET status = ?, error = ?, processed_at = COALESCE(?, processed_at)
                WHERE mailbox = ? AND uid = ?
                """,
                (status.value, error, processed_at, email.mailbox, email.uid),
            )
            if result.rowcount != 1:
                raise KeyError(f"Email {email.mailbox}:{email.uid} has not been recorded")

    def get_record(self, email: DetectedEmail) -> EmailRecord | None:
        """Return the persisted record for an email, if it exists."""
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM email_messages WHERE mailbox = ? AND uid = ?",
                (email.mailbox, email.uid),
            ).fetchone()
        if row is None:
            return None
        return EmailRecord(
            uid=row["uid"],
            mailbox=row["mailbox"],
            status=EmailProcessingStatus(row["status"]),
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
        )

    def close(self) -> None:
        """Close the SQLite connection."""
        with self._lock:
            self._connection.close()

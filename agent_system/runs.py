"""SQLite persistence for auditable agent execution records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .models import AgentExecutionRecord


class AgentRunStore:
    """Persist agent runs independently from queue job lifecycle state."""

    def __init__(self, database_path: str):
        """Open or create the agent run table in `database_path`."""
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    output TEXT,
                    error TEXT
                )
                """
            )

    def save(self, record: AgentExecutionRecord) -> None:
        """Insert or replace one execution record."""
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO agent_runs
                    (id, job_id, agent_name, status, started_at, finished_at, output, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.id),
                    str(record.job_id),
                    record.agent_name,
                    record.status,
                    record.started_at.isoformat(),
                    record.finished_at.isoformat() if record.finished_at else None,
                    json.dumps(record.output) if record.output is not None else None,
                    record.error,
                ),
            )

    def list_for_job(self, job_id: str) -> list[AgentExecutionRecord]:
        """Return execution records for one queue job in insertion order."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM agent_runs WHERE job_id = ? ORDER BY started_at ASC",
                (job_id,),
            ).fetchall()
        from datetime import datetime
        from uuid import UUID

        return [
            AgentExecutionRecord(
                id=UUID(row["id"]),
                job_id=UUID(row["job_id"]),
                agent_name=row["agent_name"],
                status=row["status"],
                started_at=datetime.fromisoformat(row["started_at"]),
                finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
                output=json.loads(row["output"]) if row["output"] else None,
                error=row["error"],
            )
            for row in rows
        ]

    def close(self) -> None:
        """Close the SQLite connection."""
        with self._lock:
            self._connection.close()

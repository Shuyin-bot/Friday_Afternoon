"""SQLite repository implementing durable job queue semantics."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from .models import ClaimedJob, Job, JobStatus, JobType


class QueueError(RuntimeError):
    """Raised when a queue operation cannot be completed safely."""


class JobNotFoundError(QueueError):
    """Raised when a requested job does not exist."""


class InvalidClaimError(QueueError):
    """Raised when a worker tries to modify a job it does not own."""


class SQLiteJobQueue:
    """Durable SQLite queue with idempotency, leases, retries, and dead letters."""

    def __init__(self, database_path: str, max_attempts: int = 3):
        """Open or create a queue database at `database_path`."""
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")
        self.max_attempts = max_attempts
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            database_path,
            timeout=30,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA busy_timeout = 30000")
        self._lock = Lock()
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create queue tables and indexes if they do not already exist."""
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    email_uid INTEGER NOT NULL,
                    mailbox TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    available_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_until TEXT,
                    last_error TEXT,
                    UNIQUE (job_type, mailbox, email_uid)
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    worker_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    outcome TEXT,
                    error TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS dead_letter_jobs (
                    job_id TEXT PRIMARY KEY,
                    failed_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    error TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS jobs_ready_idx ON jobs(status, available_at)"
            )

    def enqueue(self, job: Job) -> Job:
        """Insert a job or return the existing job for the same email and job type."""
        if job.status is not JobStatus.PENDING or job.attempts != 0:
            raise ValueError("Only new pending jobs can be enqueued")
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO jobs
                    (id, job_type, email_uid, mailbox, payload, status, attempts,
                     available_at, created_at, lease_owner, lease_until, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._job_values(job),
            )
            row = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (str(job.id),)).fetchone()
            if row is None:
                row = self._connection.execute(
                    """
                    SELECT * FROM jobs
                    WHERE job_type = ? AND mailbox = ? AND email_uid = ?
                    """,
                    (job.job_type.value, job.mailbox, job.email_uid),
                ).fetchone()
        if row is None:
            raise QueueError("Unable to persist job")
        return self._row_to_job(row)

    def claim_next(
        self,
        worker_id: str,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> ClaimedJob | None:
        """Atomically claim the oldest available job or an expired lease."""
        if not worker_id:
            raise ValueError("worker_id cannot be empty")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be greater than zero")
        current_time = now or datetime.now(timezone.utc)
        lease_until = current_time + timedelta(seconds=lease_seconds)
        current_iso = current_time.isoformat()

        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                expired_limit_jobs = self._connection.execute(
                    """
                    SELECT * FROM jobs
                    WHERE status = ? AND lease_until <= ? AND attempts >= ?
                    """,
                    (JobStatus.RUNNING.value, current_iso, self.max_attempts),
                ).fetchall()
                for expired_job in expired_limit_jobs:
                    self._mark_dead_locked(expired_job, current_time, "Worker lease expired")

                row = self._connection.execute(
                    """
                    SELECT * FROM jobs
                    WHERE (
                        status IN (?, ?) AND available_at <= ?
                    ) OR (
                        status = ? AND lease_until <= ?
                    )
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (
                        JobStatus.PENDING.value,
                        JobStatus.RETRYING.value,
                        current_iso,
                        JobStatus.RUNNING.value,
                        current_iso,
                    ),
                ).fetchone()
                if row is None:
                    self._connection.execute("COMMIT")
                    return None

                attempts = int(row["attempts"]) + 1
                if row["status"] == JobStatus.RUNNING.value:
                    self._finish_attempt(
                        row["id"],
                        row["lease_owner"],
                        current_iso,
                        "LEASE_EXPIRED",
                        "Worker lease expired",
                    )
                self._connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, attempts = ?, lease_owner = ?, lease_until = ?, last_error = NULL
                    WHERE id = ?
                    """,
                    (
                        JobStatus.RUNNING.value,
                        attempts,
                        worker_id,
                        lease_until.isoformat(),
                        row["id"],
                    ),
                )
                self._connection.execute(
                    """
                    INSERT INTO job_attempts(job_id, attempt_number, worker_id, started_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], attempts, worker_id, current_iso),
                )
                updated = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
                self._connection.execute("COMMIT")
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

        if updated is None:
            raise QueueError("Unable to read claimed job")
        return ClaimedJob(
            job=self._row_to_job(updated),
            worker_id=worker_id,
            lease_until=lease_until,
        )

    def complete(self, job_id: str, worker_id: str) -> Job:
        """Complete a leased job if it is still owned by `worker_id`."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection:
            row = self._owned_job(job_id, worker_id)
            self._connection.execute(
                """
                UPDATE jobs
                SET status = ?, lease_owner = NULL, lease_until = NULL
                WHERE id = ?
                """,
                (JobStatus.COMPLETED.value, job_id),
            )
            self._finish_attempt(job_id, worker_id, now, "COMPLETED", None)
            result = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(result or row)

    def fail(
        self,
        job_id: str,
        worker_id: str,
        error: str,
        max_attempts: int = 3,
        now: datetime | None = None,
    ) -> Job:
        """Retry a failed job or move it to the dead-letter state."""
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")
        current_time = now or datetime.now(timezone.utc)
        with self._lock, self._connection:
            row = self._owned_job(job_id, worker_id)
            attempts = int(row["attempts"])
            if attempts >= max_attempts:
                status = JobStatus.DEAD_LETTER
                available_at = current_time
                self._connection.execute(
                    """
                    INSERT OR REPLACE INTO dead_letter_jobs(job_id, failed_at, attempts, error)
                    VALUES (?, ?, ?, ?)
                    """,
                    (job_id, current_time.isoformat(), attempts, error),
                )
            else:
                status = JobStatus.RETRYING
                delay = timedelta(seconds=2 ** (attempts - 1))
                available_at = current_time + delay

            self._connection.execute(
                """
                UPDATE jobs
                SET status = ?, available_at = ?, lease_owner = NULL, lease_until = NULL, last_error = ?
                WHERE id = ?
                """,
                (status.value, available_at.isoformat(), error, job_id),
            )
            self._finish_attempt(job_id, worker_id, current_time.isoformat(), status.value, error)
            result = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if result is None:
            raise QueueError("Unable to read failed job")
        return self._row_to_job(result)

    def get(self, job_id: str) -> Job:
        """Return one job by ID."""
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(f"Job {job_id} does not exist")
        return self._row_to_job(row)

    def list_dead_letters(self) -> list[Job]:
        """Return jobs that exceeded their retry limit."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at ASC",
                (JobStatus.DEAD_LETTER.value,),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self._connection.close()

    def _owned_job(self, job_id: str, worker_id: str) -> sqlite3.Row:
        """Return a running job owned by a worker or raise a claim error."""
        row = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(f"Job {job_id} does not exist")
        if row["status"] != JobStatus.RUNNING.value or row["lease_owner"] != worker_id:
            raise InvalidClaimError(f"Worker {worker_id!r} does not own job {job_id}")
        return row

    def _finish_attempt(
        self,
        job_id: str,
        worker_id: str,
        finished_at: str,
        outcome: str,
        error: str | None,
    ) -> None:
        """Complete the latest attempt for a worker."""
        self._connection.execute(
            """
            UPDATE job_attempts
            SET finished_at = ?, outcome = ?, error = ?
            WHERE id = (
                SELECT id FROM job_attempts
                WHERE job_id = ? AND worker_id = ? AND finished_at IS NULL
                ORDER BY id DESC LIMIT 1
            )
            """,
            (finished_at, outcome, error, job_id, worker_id),
        )

    def _mark_dead_locked(self, row: sqlite3.Row, failed_at: datetime, error: str) -> None:
        """Move an expired job to dead-letter state inside an open transaction."""
        self._connection.execute(
            """
            INSERT OR REPLACE INTO dead_letter_jobs(job_id, failed_at, attempts, error)
            VALUES (?, ?, ?, ?)
            """,
            (row["id"], failed_at.isoformat(), row["attempts"], error),
        )
        self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, lease_owner = NULL, lease_until = NULL, last_error = ?
            WHERE id = ?
            """,
            (JobStatus.DEAD_LETTER.value, error, row["id"]),
        )
        if row["lease_owner"]:
            self._finish_attempt(
                row["id"],
                row["lease_owner"],
                failed_at.isoformat(),
                "DEAD_LETTER",
                error,
            )

    @staticmethod
    def _job_values(job: Job) -> tuple:
        """Convert a Pydantic job to SQLite-compatible values."""
        return (
            str(job.id),
            job.job_type.value,
            job.email_uid,
            job.mailbox,
            json.dumps(job.payload),
            job.status.value,
            job.attempts,
            job.available_at.isoformat(),
            job.created_at.isoformat(),
            job.lease_owner,
            job.lease_until.isoformat() if job.lease_until else None,
            job.last_error,
        )

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        """Convert a SQLite row back into a validated Pydantic job."""
        return Job(
            id=row["id"],
            job_type=JobType(row["job_type"]),
            email_uid=row["email_uid"],
            mailbox=row["mailbox"],
            payload=json.loads(row["payload"]),
            status=JobStatus(row["status"]),
            attempts=row["attempts"],
            available_at=datetime.fromisoformat(row["available_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            lease_owner=row["lease_owner"],
            lease_until=datetime.fromisoformat(row["lease_until"]) if row["lease_until"] else None,
            last_error=row["last_error"],
        )

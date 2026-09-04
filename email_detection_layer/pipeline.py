"""Cron-friendly email ingestion pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .config import EmailSettings
from .detector import check_new_emails_since, establish_connection
from .models import DetectedEmail
from .retriever import retrieve_email
from .state import EmailProcessingStatus, EmailStateStore
from .storage import EmailArtifactStore
from job_queue.models import Job, JobType
from job_queue.repository import SQLiteJobQueue

logger = logging.getLogger(__name__)
ConnectionFactory = Callable[[EmailSettings], tuple[bool, Any]]


class EmailIngestionPipeline:
    """Detect, retrieve, persist, and enqueue email work without running agents."""

    def __init__(
        self,
        settings: EmailSettings,
        state: EmailStateStore,
        queue: SQLiteJobQueue,
        artifacts: EmailArtifactStore,
        connection_factory: ConnectionFactory = establish_connection,
    ):
        """Create an ingestion pipeline with explicit storage and IMAP dependencies."""
        self.settings = settings
        self.state = state
        self.queue = queue
        self.artifacts = artifacts
        self.connection_factory = connection_factory

    def run(self) -> int:
        """Process available messages and return the number of jobs enqueued."""
        connected, imap = self.connection_factory(self.settings)
        if not connected or imap is None:
            raise RuntimeError(
                f"Unable to connect or authenticate to {self.settings.imap_host}:{self.settings.imap_port}"
            )

        try:
            messages = self._messages_to_process(imap)
            enqueued = 0
            for email in messages:
                try:
                    if self._process_email(imap, email):
                        enqueued += 1
                except Exception as error:
                    logger.exception("Failed to ingest %s:%s", email.mailbox, email.uid)
                    self._mark_failed(email, error)
            return enqueued
        finally:
            try:
                imap.logout()
            except Exception:
                logger.warning("Unable to cleanly close the IMAP connection", exc_info=True)

    def _messages_to_process(self, imap: Any) -> list[DetectedEmail]:
        """Combine retryable records with new UID detections without duplicates."""
        mailbox = self.settings.mailbox
        last_uid = self.state.get_last_queued_uid(mailbox)
        detected = check_new_emails_since(imap, mailbox, last_uid)
        for email in detected:
            self.state.record_detected(email)

        messages = {email.uid: email for email in self.state.list_retryable(mailbox)}
        return [messages[uid] for uid in sorted(messages)]

    def _process_email(self, imap: Any, email: DetectedEmail) -> bool:
        """Retrieve, persist, enqueue, and mark one email as queued."""
        retrieved = retrieve_email(imap, email)
        raw_path, normalized_path = self.artifacts.save(retrieved)
        self.state.set_status(email, EmailProcessingStatus.RETRIEVED)
        job = Job(
            job_type=JobType.EMAIL_RECEIVED,
            email_uid=email.uid,
            mailbox=email.mailbox,
            payload={
                "raw_email_path": str(raw_path),
                "normalized_email_path": str(normalized_path),
                "message_id": retrieved.message_id,
            },
        )
        self.queue.enqueue(job)
        self.state.mark_queued(email)
        logger.info("Enqueued email %s:%s", email.mailbox, email.uid)
        return True

    def _mark_failed(self, email: DetectedEmail, error: Exception) -> None:
        """Record a per-message failure without stopping other messages."""
        try:
            self.state.set_status(email, EmailProcessingStatus.FAILED, str(error))
        except KeyError:
            logger.error("Could not record failure for untracked email %s:%s", email.mailbox, email.uid)


def main() -> None:
    """Run one cron ingestion cycle using environment configuration."""
    logging.basicConfig(level=logging.INFO)
    settings = EmailSettings.from_env()
    state = EmailStateStore(settings.state_db_path)
    queue = SQLiteJobQueue(settings.state_db_path)
    try:
        pipeline = EmailIngestionPipeline(
            settings,
            state,
            queue,
            EmailArtifactStore(settings.data_dir),
        )
        count = pipeline.run()
        logger.info("Ingestion cycle completed: %d job(s) enqueued", count)
    finally:
        queue.close()
        state.close()


if __name__ == "__main__":
    main()

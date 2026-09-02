"""Worker loop for consuming jobs and invoking Python handlers."""

from __future__ import annotations

import logging
import time
from threading import Event

from .dispatcher import JobDispatcher
from .repository import SQLiteJobQueue

logger = logging.getLogger(__name__)


class QueueWorker:
    """Claim jobs from SQLite and dispatch them with retry-aware completion."""

    def __init__(
        self,
        queue: SQLiteJobQueue,
        dispatcher: JobDispatcher,
        worker_id: str,
        max_attempts: int = 3,
    ):
        """Create a worker with a stable identity and handler dispatcher."""
        if not worker_id:
            raise ValueError("worker_id cannot be empty")
        self.queue = queue
        self.dispatcher = dispatcher
        self.worker_id = worker_id
        self.max_attempts = max_attempts

    def run_once(self) -> bool:
        """Process one available job and return whether work was performed."""
        claimed = self.queue.claim_next(self.worker_id)
        if claimed is None:
            return False
        try:
            self.dispatcher.dispatch(claimed.job)
        except Exception as error:
            logger.exception("Job %s failed", claimed.job.id)
            self.queue.fail(str(claimed.job.id), self.worker_id, str(error), self.max_attempts)
        else:
            self.queue.complete(str(claimed.job.id), self.worker_id)
        return True

    def run_forever(self, stop_event: Event | None = None, poll_interval: float = 1.0) -> None:
        """Poll until `stop_event` is set, sleeping when no work is available."""
        stop_event = stop_event or Event()
        while not stop_event.is_set():
            if not self.run_once():
                stop_event.wait(poll_interval)

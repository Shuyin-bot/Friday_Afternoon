"""Queue worker adapter for the quotation workflow."""

from __future__ import annotations

from job_queue.dispatcher import JobDispatcher
from job_queue.models import JobType
from job_queue.repository import SQLiteJobQueue
from job_queue.worker import QueueWorker

from .workflow import QuotationWorkflow


class WorkflowWorker:
    """Consume all quotation workflow jobs and delegate them to `QuotationWorkflow`."""

    def __init__(self, queue: SQLiteJobQueue, workflow: QuotationWorkflow, worker_id: str, max_attempts: int = 3):
        """Create a queue worker that handles every supported workflow job type."""
        dispatcher = JobDispatcher()
        dispatcher.register(JobType.EMAIL_RECEIVED.value, workflow.handle)
        for job_type in workflow.agent_names:
            dispatcher.register(job_type, workflow.handle)
        self._worker = QueueWorker(queue, dispatcher, worker_id, max_attempts)

    def run_once(self) -> bool:
        """Claim and process one workflow job."""
        return self._worker.run_once()

    def run_forever(self, *args, **kwargs) -> None:
        """Run the underlying queue worker until its stop event is set."""
        self._worker.run_forever(*args, **kwargs)

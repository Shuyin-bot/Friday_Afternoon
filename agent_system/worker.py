"""Queue worker adapter for running registered Python agents."""

from __future__ import annotations

from job_queue.dispatcher import JobDispatcher
from job_queue.models import Job
from job_queue.repository import SQLiteJobQueue
from job_queue.worker import QueueWorker

from .models import AgentContext
from .runner import AgentRunner


class AgentWorker:
    """Connect queue jobs to explicitly mapped agents without embedding workflow policy."""

    def __init__(
        self,
        queue: SQLiteJobQueue,
        runner: AgentRunner,
        worker_id: str,
        job_agents: dict[str, str],
        max_attempts: int = 3,
    ):
        """Create an agent worker with a job-type to agent-name mapping."""
        self.runner = runner
        self.job_agents = job_agents
        dispatcher = JobDispatcher()
        for job_type in job_agents:
            dispatcher.register(job_type, self._handle)
        self.queue_worker = QueueWorker(queue, dispatcher, worker_id, max_attempts)

    def run_once(self) -> bool:
        """Process one queued job through its mapped agent."""
        return self.queue_worker.run_once()

    async def _run_agent(self, job: Job) -> None:
        """Build agent context from the job payload and execute its mapped agent."""
        agent_name = self.job_agents[job.job_type.value]
        await self.runner.run(
            agent_name,
            AgentContext(job=job, input_data=job.payload, attempt=job.attempts),
        )

    def _handle(self, job: Job) -> object:
        """Return the coroutine consumed by the queue dispatcher."""
        return self._run_agent(job)

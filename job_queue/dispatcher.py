"""Dispatch queued jobs to explicitly registered Python handlers."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable

from .models import Job

JobHandler = Callable[[Job], object]


class UnknownJobTypeError(RuntimeError):
    """Raised when no handler has been registered for a job type."""


class JobDispatcher:
    """Map job types to Python functions or async functions."""

    def __init__(self, handlers: dict[str, JobHandler] | None = None):
        """Create a dispatcher with an optional initial handler mapping."""
        self._handlers = handlers or {}

    def register(self, job_type: str, handler: JobHandler) -> None:
        """Register or replace the handler for a job type."""
        self._handlers[job_type] = handler

    def dispatch(self, job: Job) -> None:
        """Execute the handler for a job, including async handlers."""
        handler = self._handlers.get(job.job_type.value)
        if handler is None:
            raise UnknownJobTypeError(f"No handler registered for {job.job_type.value}")
        result = handler(job)
        if inspect.isawaitable(result):
            asyncio.run(result)

"""Pydantic contracts for the asynchronous job queue."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class JobType(str, Enum):
    """Types of work that can be processed by agent workers."""

    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    CLASSIFY_EMAIL = "CLASSIFY_EMAIL"
    EXTRACT_QUOTATION = "EXTRACT_QUOTATION"
    RESEARCH_PRODUCTS = "RESEARCH_PRODUCTS"
    GENERATE_DRAFT = "GENERATE_DRAFT"


class JobStatus(str, Enum):
    """Lifecycle states for a queued job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class Job(BaseModel):
    """Serializable unit of work consumed by an agent worker."""

    model_config = ConfigDict(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4)
    job_type: JobType
    email_uid: int = Field(gt=0)
    mailbox: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    attempts: int = Field(default=0, ge=0)
    available_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lease_owner: str | None = None
    lease_until: datetime | None = None
    last_error: str | None = None


class ClaimedJob(BaseModel):
    """A job currently leased to one worker."""

    model_config = ConfigDict(frozen=True)

    job: Job
    worker_id: str = Field(min_length=1)
    lease_until: datetime

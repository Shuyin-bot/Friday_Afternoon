"""Pydantic contracts shared by the Python agent framework."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from job_queue.models import Job


class AgentRiskLevel(str, Enum):
    """Risk classification used to constrain agent capabilities."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AgentContext(BaseModel):
    """Validated input context supplied to one agent execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    job: Job
    input_data: dict[str, Any] = Field(default_factory=dict)
    prior_outputs: dict[str, Any] = Field(default_factory=dict)
    attempt: int = Field(default=1, ge=1)


class AgentExecutionRecord(BaseModel):
    """Auditable record of an agent attempt."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    agent_name: str = Field(min_length=1)
    status: str = Field(pattern="^(RUNNING|COMPLETED|FAILED)$")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class AgentMetadata(BaseModel):
    """Static capability declaration for an agent."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    allowed_tools: tuple[str, ...] = ()
    retry_limit: int = Field(default=1, ge=0)
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW

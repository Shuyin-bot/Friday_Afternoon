from datetime import datetime
from enum import Enum as PythonEnum

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_contexts.base import Base


class AgentSessionStatus(str, PythonEnum):
    ACTIVE = "ACTIVE"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    READY_TO_RESUME = "READY_TO_RESUME"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    queued_job_id: Mapped[int] = mapped_column(
        ForeignKey("queued_jobs.id"), nullable=False, unique=True, index=True
    )
    status: Mapped[AgentSessionStatus] = mapped_column(
        Enum(AgentSessionStatus),
        default=AgentSessionStatus.ACTIVE,
        nullable=False,
    )
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    message_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    queued_job = relationship("QueuedJob")

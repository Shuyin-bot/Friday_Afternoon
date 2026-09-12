from datetime import datetime
from enum import Enum as PythonEnum
from db_contexts.base import Base
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RetrievedEmail(Base):
    __tablename__ = "retrieved_email"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    from_email: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(998), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    queued_jobs: Mapped[list["QueuedJob"]] = relationship(back_populates="email")


class JobStatus(str, PythonEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class QueuedJob(Base):
    __tablename__ = "queued_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False
    )
    email_id: Mapped[int] = mapped_column(
        ForeignKey("retrieved_email.id"), nullable=False, index=True
    )
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    email: Mapped[RetrievedEmail] = relationship(back_populates="queued_jobs")

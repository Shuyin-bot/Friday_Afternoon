from datetime import datetime
from enum import Enum as PythonEnum

from db_contexts.base import Base
from .email_retriever_models import QueuedJob
from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class HumanRequestType(str, PythonEnum):
    CLARIFICATION = "CLARIFICATION"
    APPROVAL = "APPROVAL"
    PRODUCT_SELECTION = "PRODUCT_SELECTION"
    PRICE_CONFIRMATION = "PRICE_CONFIRMATION"


class HumanRequestStatus(str, PythonEnum):
    PENDING = "PENDING"
    ANSWERED = "ANSWERED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class HumanRequest(Base):
    __tablename__ = "human_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    queued_job_id: Mapped[int] = mapped_column(
        ForeignKey("queued_jobs.id"), nullable=False, index=True
    )
    request_type: Mapped[HumanRequestType] = mapped_column(
        Enum(HumanRequestType), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[HumanRequestStatus] = mapped_column(
        Enum(HumanRequestStatus), default=HumanRequestStatus.PENDING, nullable=False
    )
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    queued_job: Mapped[QueuedJob] = relationship()

from datetime import datetime

from db_contexts.base import Base
from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class CompanyResearch(Base):
    __tablename__ = "company_research"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sources: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    researched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

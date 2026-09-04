"""Pydantic contracts for email ingestion."""

from pydantic import BaseModel, ConfigDict, Field


class DetectedEmail(BaseModel):
    """Reference to an email discovered in an IMAP mailbox."""

    model_config = ConfigDict(frozen=True)

    uid: int = Field(gt=0)
    mailbox: str = Field(min_length=1)

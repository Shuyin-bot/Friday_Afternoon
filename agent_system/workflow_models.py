"""Typed data contracts for the quotation workflow."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    """Persisted state of one quotation request."""

    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    EXTRACTED = "EXTRACTED"
    VERIFIED = "VERIFIED"
    RESEARCHED = "RESEARCHED"
    QUOTE_PREPARED = "QUOTE_PREPARED"
    DRAFT_READY = "DRAFT_READY"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    NOT_A_QUOTATION = "NOT_A_QUOTATION"
    SECURITY_REVIEW = "SECURITY_REVIEW"


class QuotationRequest(BaseModel):
    """Structured quotation requirements extracted from an email."""

    model_config = ConfigDict(frozen=True)

    is_quotation_request: bool = True
    customer_name: str | None = None
    products: list[str] = Field(default_factory=list)
    quantities: list[str] = Field(default_factory=list)
    delivery_location: str | None = None
    delivery_date: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    security_flags: list[str] = Field(default_factory=list)
    explanation: str = ""


class SenderVerification(BaseModel):
    """Result of sender checks; this is not proof of identity."""

    model_config = ConfigDict(frozen=True)

    is_trusted: bool
    confidence: float = Field(ge=0, le=1)
    signals: list[str] = Field(default_factory=list)
    requires_human_review: bool = True
    explanation: str = ""


class ProductResearch(BaseModel):
    """Product research result, without authoritative pricing claims in M9."""

    model_config = ConfigDict(frozen=True)

    products_found: list[str] = Field(default_factory=list)
    unresolved_products: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    requires_tooling: bool = True
    explanation: str = ""


class QuoteLine(BaseModel):
    """One line in a prepared quotation."""

    product: str
    quantity: str
    unit_price: float | None = None
    line_total: float | None = None


class PreparedQuote(BaseModel):
    """Quotation structure awaiting trusted product and pricing data."""

    model_config = ConfigDict(frozen=True)

    lines: list[QuoteLine] = Field(default_factory=list)
    currency: str | None = None
    total: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class EmailDraft(BaseModel):
    """Customer-facing draft that must be approved before sending."""

    model_config = ConfigDict(frozen=True)

    subject: str
    body: str
    approved: bool = False
    assumptions: list[str] = Field(default_factory=list)


class WorkflowPayload(BaseModel):
    """Envelope passed between workflow jobs."""

    model_config = ConfigDict(extra="allow")

    email: dict[str, Any] = Field(default_factory=dict)
    classification: dict[str, Any] | None = None
    quotation_request: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    research: dict[str, Any] | None = None
    quote: dict[str, Any] | None = None
    draft: dict[str, Any] | None = None

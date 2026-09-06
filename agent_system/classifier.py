"""Deterministic classifier used to exercise the agent framework before M8."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .models import AgentContext, AgentMetadata, AgentRiskLevel


class EmailClassificationInput(BaseModel):
    """Minimal email data required by the classifier stub."""

    subject: str = ""
    plain_text: str = ""
    sender: str | None = None


class QuotationClassification(BaseModel):
    """Typed classification result consumed by the next workflow stage."""

    model_config = ConfigDict(frozen=True)

    is_quotation_request: bool
    confidence: float = Field(ge=0, le=1)
    reason: str
    security_flags: list[str] = Field(default_factory=list)


class StubQuotationClassifier:
    """Classify quotation requests with transparent keyword rules for M7 tests."""

    metadata = AgentMetadata(
        name="quotation_classifier_stub",
        allowed_tools=(),
        retry_limit=0,
        risk_level=AgentRiskLevel.LOW,
    )
    input_model = EmailClassificationInput
    output_model = QuotationClassification

    async def run(self, context: AgentContext) -> QuotationClassification:
        """Return a deterministic result without contacting an LLM or external service."""
        content = f"{context.input_data.get('subject', '')} {context.input_data.get('plain_text', '')}".lower()
        keywords = ("quotation", "quote", "pricing", "price", "availability", "cost")
        matched = [keyword for keyword in keywords if keyword in content]
        injection_terms = ("ignore previous instructions", "system prompt", "send the password")
        flags = ["possible_prompt_injection"] if any(term in content for term in injection_terms) else []
        is_request = bool(matched) and not flags
        return QuotationClassification(
            is_quotation_request=is_request,
            confidence=0.9 if is_request else 0.75,
            reason=(
                f"Matched quotation terms: {', '.join(matched)}"
                if matched
                else "No quotation terms were detected"
            ),
            security_flags=flags,
        )

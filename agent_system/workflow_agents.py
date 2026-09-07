"""Deterministic workflow agents used until tool integrations are added in M10."""

from __future__ import annotations

import re

from .classifier import EmailClassificationInput, QuotationClassification
from .models import AgentContext, AgentMetadata, AgentRiskLevel
from .workflow_models import (
    EmailDraft,
    PreparedQuote,
    ProductResearch,
    QuotationRequest,
    SenderVerification,
)


class StubQuotationExtractor:
    """Extract basic quotation fields with transparent rules for local testing."""

    metadata = AgentMetadata(name="quotation_extractor_stub", risk_level=AgentRiskLevel.LOW, retry_limit=0)
    input_model = EmailClassificationInput
    output_model = QuotationRequest

    async def run(self, context: AgentContext) -> QuotationRequest:
        """Extract simple product and quantity patterns without an LLM."""
        text = context.input_data.get("plain_text", "")
        products = re.findall(r"(?:for|of)\s+(?:\d+\s+)?([A-Za-z][A-Za-z0-9 -]{2,40})", text, re.IGNORECASE)
        quantity_matches = re.findall(r"\b(\d+)\s*(?:x|units?|pieces?)\b", text, re.IGNORECASE)
        products = [product.strip(" .,") for product in products[:10]]
        return QuotationRequest(
            products=products,
            quantities=quantity_matches[:10],
            missing_information=["customer_name"] if not context.input_data.get("sender") else [],
            explanation="Extracted fields using the M9 deterministic extractor.",
        )


class StubSenderVerifier:
    """Perform only a basic sender-presence check; never claims strong identity."""

    metadata = AgentMetadata(name="sender_verifier_stub", risk_level=AgentRiskLevel.MEDIUM, retry_limit=0)
    input_model = EmailClassificationInput
    output_model = SenderVerification

    async def run(self, context: AgentContext) -> SenderVerification:
        """Return a low-confidence result that requires human review."""
        sender = context.input_data.get("sender")
        return SenderVerification(
            is_trusted=bool(sender),
            confidence=0.5 if sender else 0.0,
            signals=["sender_present"] if sender else [],
            requires_human_review=True,
            explanation="M9 does not yet integrate technical or business identity checks.",
        )


class StubProductResearcher:
    """Represent product research as unresolved until M10 tools are available."""

    metadata = AgentMetadata(name="product_research_stub", risk_level=AgentRiskLevel.MEDIUM, retry_limit=0)
    input_model = QuotationRequest
    output_model = ProductResearch

    async def run(self, context: AgentContext) -> ProductResearch:
        """Return requested products as unresolved and require tool-backed research."""
        products = context.input_data.get("products", [])
        return ProductResearch(
            unresolved_products=products,
            requires_tooling=True,
            explanation="No product catalogue or pricing tool is enabled in M9.",
        )


class StubQuotePreparer:
    """Create a quote skeleton without inventing prices."""

    metadata = AgentMetadata(name="quote_preparer_stub", risk_level=AgentRiskLevel.HIGH, retry_limit=0)
    input_model = ProductResearch
    output_model = PreparedQuote

    async def run(self, context: AgentContext) -> PreparedQuote:
        """Create unpriced lines and explicitly retain human-review requirements."""
        products = context.input_data.get("unresolved_products", [])
        return PreparedQuote(
            lines=[{"product": product, "quantity": "unspecified"} for product in products],
            assumptions=["Prices and availability require trusted product tools."],
        )


class StubEmailDrafter:
    """Create an unapproved draft from the workflow payload."""

    metadata = AgentMetadata(name="email_drafter_stub", risk_level=AgentRiskLevel.HIGH, retry_limit=0)
    input_model = PreparedQuote
    output_model = EmailDraft

    async def run(self, context: AgentContext) -> EmailDraft:
        """Generate a review-only draft that cannot be sent automatically."""
        return EmailDraft(
            subject="Re: Request for quotation",
            body="Thank you for your request. Your quotation is being reviewed.",
            assumptions=context.input_data.get("assumptions", []),
        )

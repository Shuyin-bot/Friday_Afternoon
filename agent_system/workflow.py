"""Explicit Python orchestration for the quotation workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from job_queue.models import Job, JobType
from job_queue.repository import SQLiteJobQueue

from .models import AgentContext
from .runner import AgentRunner
from .classifier import QuotationClassification
from .workflow_models import (
    EmailDraft,
    PreparedQuote,
    ProductResearch,
    QuotationRequest,
    SenderVerification,
    WorkflowStatus,
)
from .workflow_store import WorkflowStore


class WorkflowConfigurationError(ValueError):
    """Raised when the workflow has no agent mapping for a stage."""


class QuotationWorkflow:
    """Process one queue job and enqueue the next validated workflow stage."""

    def __init__(
        self,
        queue: SQLiteJobQueue,
        runner: AgentRunner,
        store: WorkflowStore,
        agent_names: dict[str, str],
        minimum_classification_confidence: float = 0.7,
    ):
        """Create workflow orchestration with explicit queue, runner, and stage dependencies."""
        if not 0 <= minimum_classification_confidence <= 1:
            raise ValueError("minimum_classification_confidence must be between zero and one")
        self.queue = queue
        self.runner = runner
        self.store = store
        self.agent_names = agent_names
        self.minimum_classification_confidence = minimum_classification_confidence

    async def handle(self, job: Job) -> None:
        """Process a single stage and persist its transition or terminal result."""
        if job.job_type is JobType.EMAIL_RECEIVED:
            await self._handle_received(job)
        elif job.job_type is JobType.CLASSIFY_EMAIL:
            await self._handle_classification(job)
        elif job.job_type is JobType.EXTRACT_QUOTATION:
            await self._handle_extraction(job)
        elif job.job_type is JobType.VERIFY_SENDER:
            await self._handle_verification(job)
        elif job.job_type is JobType.RESEARCH_PRODUCTS:
            await self._handle_research(job)
        elif job.job_type is JobType.PREPARE_QUOTE:
            await self._handle_quote(job)
        elif job.job_type is JobType.GENERATE_DRAFT:
            await self._handle_draft(job)
        else:
            raise WorkflowConfigurationError(f"Unsupported workflow job type: {job.job_type.value}")

    async def _handle_received(self, job: Job) -> None:
        """Load the normalized email artifact and enqueue classification."""
        payload = dict(job.payload)
        normalized_path = payload.get("normalized_email_path")
        if not normalized_path:
            raise WorkflowConfigurationError("EMAIL_RECEIVED job has no normalized_email_path")
        try:
            email = json.loads(Path(normalized_path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise WorkflowConfigurationError(f"Unable to load normalized email: {error}") from error
        next_payload = {"email": email, **email}
        self.store.save(job.mailbox, job.email_uid, WorkflowStatus.EMAIL_RECEIVED, next_payload)
        self._enqueue(job, JobType.CLASSIFY_EMAIL, next_payload)

    async def _handle_classification(self, job: Job) -> None:
        """Run classification and stop or continue based on confidence and security flags."""
        payload = dict(job.payload)
        result = await self._run(job, "CLASSIFY_EMAIL", payload)
        classification = QuotationClassification.model_validate(result)
        payload["classification"] = classification.model_dump()
        if classification.security_flags:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.SECURITY_REVIEW, payload)
        elif not classification.is_quotation_request:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NOT_A_QUOTATION, payload)
        elif classification.confidence < self.minimum_classification_confidence:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NEEDS_HUMAN_REVIEW, payload)
        else:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.CLASSIFIED, payload)
            self._enqueue(job, JobType.EXTRACT_QUOTATION, payload)

    async def _handle_extraction(self, job: Job) -> None:
        """Extract requirements and stop when required information is missing."""
        payload = dict(job.payload)
        result = await self._run(job, "EXTRACT_QUOTATION", payload)
        request = QuotationRequest.model_validate(result)
        payload["quotation_request"] = request.model_dump()
        if request.missing_information:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NEEDS_CLARIFICATION, payload)
        else:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.EXTRACTED, payload)
            self._enqueue(job, JobType.VERIFY_SENDER, payload)

    async def _handle_verification(self, job: Job) -> None:
        """Run sender checks and require review for untrusted or incomplete verification."""
        payload = dict(job.payload)
        result = await self._run(job, "VERIFY_SENDER", payload)
        verification = SenderVerification.model_validate(result)
        payload["verification"] = verification.model_dump()
        if not verification.is_trusted or verification.requires_human_review:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NEEDS_HUMAN_REVIEW, payload)
        else:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.VERIFIED, payload)
            self._enqueue(job, JobType.RESEARCH_PRODUCTS, payload)

    async def _handle_research(self, job: Job) -> None:
        """Run research and stop until trusted product tools are available."""
        payload = dict(job.payload)
        request = QuotationRequest.model_validate(payload["quotation_request"])
        result = await self._run(job, "RESEARCH_PRODUCTS", request.model_dump())
        research = ProductResearch.model_validate(result)
        payload["research"] = research.model_dump()
        if research.requires_tooling or research.unresolved_products:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NEEDS_HUMAN_REVIEW, payload)
        else:
            self.store.save(job.mailbox, job.email_uid, WorkflowStatus.RESEARCHED, payload)
            self._enqueue(job, JobType.PREPARE_QUOTE, payload)

    async def _handle_quote(self, job: Job) -> None:
        """Prepare a quote only from the validated research result."""
        payload = dict(job.payload)
        result = await self._run(job, "PREPARE_QUOTE", payload["research"])
        quote = PreparedQuote.model_validate(result)
        payload["quote"] = quote.model_dump()
        self.store.save(job.mailbox, job.email_uid, WorkflowStatus.QUOTE_PREPARED, payload)
        self._enqueue(job, JobType.GENERATE_DRAFT, payload)

    async def _handle_draft(self, job: Job) -> None:
        """Generate and persist an explicitly unapproved customer draft."""
        payload = dict(job.payload)
        result = await self._run(job, "GENERATE_DRAFT", payload["quote"])
        draft = EmailDraft.model_validate(result)
        payload["draft"] = draft.model_dump()
        self.store.save(job.mailbox, job.email_uid, WorkflowStatus.NEEDS_HUMAN_REVIEW, payload)

    async def _run(self, job: Job, stage: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the configured agent for a stage and return its serialized output."""
        agent_name = self.agent_names.get(stage)
        if not agent_name:
            raise WorkflowConfigurationError(f"No agent configured for {stage}")
        output = await self.runner.run(
            agent_name,
            AgentContext(job=job, input_data=input_data, attempt=job.attempts),
        )
        return output.model_dump()

    def _enqueue(self, job: Job, job_type: JobType, payload: dict[str, Any]) -> Job:
        """Enqueue one next-stage job for the same email."""
        return self.queue.enqueue(
            Job(
                job_type=job_type,
                email_uid=job.email_uid,
                mailbox=job.mailbox,
                payload=payload,
            )
        )

from db_contexts.models import AgentSessionStatus, JobStatus
from db_contexts.repos.agent_session_repository import (
    get_agent_session_by_job_id,
    get_or_create_agent_session,
    update_agent_session,
)
from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.repos.human_request_repository import get_human_request
from db_contexts.repos.product_repository import get_product_by_sku, search_products
from .agents.classifier import get_classifying_agent
from .agents.core_agent import get_core_agent
from .agents.core_models import CoreAgentDependencies
import asyncio
import os
from pydantic_ai.agent import Agent
from pathlib import Path
import json
from pydantic_ai import ModelMessagesTypeAdapter, RunCancelled


def get_path_to_email(email_external_id) -> Path:
    return Path.joinpath(Path.cwd(), "data", "emails", f"{email_external_id}_email.json")


def _load_meta(job) -> dict:
    """Load and return the job's meta_data as a dict, tolerating empty/missing data."""
    try:
        return json.loads(job.meta_data or "{}")
    except json.JSONDecodeError:
        return {}


def _save_meta(job, meta: dict, status: JobStatus) -> None:
    update_queued_job(job.id, status, json.dumps(meta))


async def classify_emails():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")
    classifier = get_classifying_agent()

    for job in jobs:
        # job.email_id is the FK to retrieved_email.id (internal PK), not
        # the external email_id the retriever/seeder used for the filename
        # — use job.email.email_id instead (see get_queued_jobs_by_stat).
        file_path = get_path_to_email(job.email.email_id)
        email_data = json.loads(file_path.read_text())
        res = await classifier.run(email_data.get('content'))

        meta = _load_meta(job)
        meta["classification"] = res.output.model_dump_json()
        print(meta)

        if not res.output.is_quote:
            _save_meta(job, meta, JobStatus.NOT_QUOTATION)
            # file_path.unlink()
            continue
        _save_meta(job, meta, JobStatus.CLASSIFIED)


async def run_core():
    jobs = get_queued_jobs_by_stat(JobStatus.CLASSIFIED)
    for job in jobs:
        agent_session = get_or_create_agent_session(job.id)
        email_path = get_path_to_email(job.email.email_id)
        email_data = json.loads(email_path.read_text())

        is_resume = agent_session.status == AgentSessionStatus.READY_TO_RESUME
        if is_resume:
            print(
                f"resuming job {job.id} from agent session "
                f"{agent_session.id} at {agent_session.current_step or 'unknown step'}"
            )
        else:
            print(f"starting agent session {agent_session.id} for job {job.id}")

        try:
            update_agent_session(
                session_id=agent_session.id,
                status=AgentSessionStatus.ACTIVE,
                current_step="core_agent",
            )

            prompt = email_data.get("content")
            if is_resume:
                request_id = (agent_session.summary or {}).get("human_request_id")
                request = get_human_request(request_id) if request_id else None
                resume_instructions = []
                if request and request.answer:
                    resume_instructions.append(
                        "The human reviewer answered your previous question: "
                        f"{request.answer}"
                    )
                review_feedback = (agent_session.summary or {}).get("review_feedback")
                if review_feedback:
                    resume_instructions.append(
                        "The human reviewer sent the draft back with this feedback: "
                        f"{review_feedback}"
                    )
                if resume_instructions:
                    prompt = (
                        "Continue from the saved conversation. Apply the following "
                        "human review information before producing the next result:\n"
                        + "\n".join(resume_instructions)
                    )

            message_history = ModelMessagesTypeAdapter.validate_python(
                agent_session.message_history or []
            )
            deps = CoreAgentDependencies(
                job_id=job.id,
                session_id=agent_session.id,
                session_summary=agent_session.summary or {},
            )
            agent = get_core_agent()
            res = await agent.run(
                prompt,
                deps=deps,
                message_history=message_history or None,
            )
            meta = _load_meta(job)
            meta["draft"] = res.output.model_dump_json()
            update_agent_session(
                session_id=agent_session.id,
                status=AgentSessionStatus.COMPLETED,
                current_step="draft_created",
                summary={
                    **(agent_session.summary or {}),
                    "last_action": "draft_created",
                },
                message_history=json.loads(res.all_messages_json().decode()),
            )
            print(meta)
            _save_meta(job, meta, JobStatus.DRAFTED)
        except RunCancelled as cancellation:
            current_session = get_agent_session_by_job_id(job.id)
            if not current_session or not (current_session.summary or {}).get(
                "human_request_id"
            ):
                raise

            session_messages = json.loads(cancellation.all_messages_json().decode())
            update_agent_session(
                session_id=current_session.id,
                status=AgentSessionStatus.WAITING_FOR_HUMAN,
                current_step="human_input",
                message_history=session_messages,
            )
            meta = _load_meta(job)
            meta["human_request_id"] = (current_session.summary or {}).get(
                "human_request_id"
            )
            _save_meta(job, meta, JobStatus.WAITING_FOR_INPUT)
        except Exception as error:
            update_agent_session(
                session_id=agent_session.id,
                status=AgentSessionStatus.FAILED,
                current_step="failed",
                last_error=str(error),
            )
            meta = _load_meta(job)
            meta["error"] = str(error)
            _save_meta(job, meta, JobStatus.FAILED)


async def main():
    await classify_emails()
    await run_core()

if __name__ == "__main__":
    asyncio.run(main())

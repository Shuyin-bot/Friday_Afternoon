from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.repos.product_repository import get_product_by_sku, search_products
from db_contexts.models.email_retriever_models import JobStatus
from .agents.classifier import get_classifying_agent
from .agents.core_agent import get_core_agent
import asyncio
import os
from pydantic_ai.agent import Agent
from pathlib import Path
import json


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
            _save_meta(job, meta, JobStatus.COMPLETED)
            # file_path.unlink()
            continue
        _save_meta(job, meta, JobStatus.CLASSIFIED)


async def run_core():
    jobs = get_queued_jobs_by_stat(JobStatus.CLASSIFIED)
    agent = get_core_agent()
    for job in jobs:
        email_str = get_path_to_email(job.email_id).read_text()
        await agent.run(email_str)
        break


async def main():
    await classify_emails()
    await run_core()

if __name__ == "__main__":
    asyncio.run(main())

from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.models.email_retriever_models import JobStatus
from .agents.classifier import get_classifying_agent
from .agents.extractor_agent import get_extractor_agent
from .agents.external_research_agent import get_external_research_agent
from .agents.product_catalog_research_agent import get_internal_research_agent
from .agents.email_draft_agent import get_email_draft_agent
import asyncio
import os
from pydantic_ai.agent import Agent
from pathlib import Path
import json


def get_path_to_email(email_id) -> Path:
    return Path.joinpath(Path.cwd(), "data", "emails", f"{email_id}_email.json")


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
        file_path = get_path_to_email(job.email_id)
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


async def extract_quotations():
    quotation_emails = get_queued_jobs_by_stat(JobStatus.CLASSIFIED)
    print(f"extracting quote from {len(quotation_emails)} emails")
    extractor = get_extractor_agent()

    for job in quotation_emails:
        file_path = get_path_to_email(job.email_id)
        email_data = json.loads(file_path.read_text())
        res = await extractor.run(email_data.get("content"))

        meta = _load_meta(job)
        meta["extraction"] = res.output.model_dump_json()
        print(meta)
        _save_meta(job, meta, JobStatus.EXTRACTED)


async def research_companies():
    jobs = get_queued_jobs_by_stat(JobStatus.EXTRACTED)
    print(f"researching {len(jobs)} companies")
    researcher = get_external_research_agent()
    tavily_key_present = bool(os.getenv("TAVILY_API_KEY"))

    for job in jobs:
        meta = _load_meta(job)
        extraction = json.loads(meta.get("extraction", "{}"))
        company = extraction.get("company")

        if not company:
            meta["external_research_skipped"] = "no company extracted"
        elif not tavily_key_present:
            meta["external_research_skipped"] = "TAVILY_API_KEY not configured"
        else:
            res = await researcher.run(f"Research this company: {company}")
            meta["external_research"] = res.output.model_dump_json()

        print(meta)
        # Always advance the job so a missing field cannot stall the pipeline.
        _save_meta(job, meta, JobStatus.RESEARCH_EXT)


async def research_products():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_EXT)
    print(f"researching {len(jobs)} products")
    researcher = get_internal_research_agent()

    for job in jobs:
        meta = _load_meta(job)
        extraction = json.loads(meta.get("extraction", "{}"))
        product = extraction.get("product")

        if not product:
            meta["internal_research_skipped"] = "no product extracted"
        else:
            res = await researcher.run(f"Find this product in the catalog: {product}")
            meta["internal_research"] = res.output.model_dump_json()

        print(meta)
        _save_meta(job, meta, JobStatus.RESEARCH_INT)


async def draft_emails():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_INT)
    print(f"drafting {len(jobs)} emails")
    drafter = get_email_draft_agent()

    for job in jobs:
        meta = _load_meta(job)
        research = meta.get("internal_research")

        if not research:
            meta["draft_skipped"] = "no internal research available"
        else:
            res = await drafter.run(
                f"Write a quotation email using this catalog research: {research}"
            )
            meta["draft"] = res.output.model_dump_json()

        print(meta)
        _save_meta(job, meta, JobStatus.DRAFTED)


async def main():
    await classify_emails()
    await extract_quotations()
    await research_companies()
    await research_products()
    await draft_emails()

if __name__ == "__main__":
    asyncio.run(main())

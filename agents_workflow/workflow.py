from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.models.email_retriever_models import JobStatus
from .agents.classifier import get_classifying_agent
from .agents.extractor_agent import get_extractor_agent
from .agents.external_research_agent import get_external_research_agent
from .agents.product_catalog_research_agent import get_internal_research_agent
from .agents.email_draft_agent import get_email_draft_agent
import asyncio
from pydantic_ai.agent import Agent
from pathlib import Path
import json


def get_path_to_email(email_id) -> Path:
    return Path.joinpath(Path.cwd(), "data", "emails", f"{email_id}_email.json")


async def classify_emails():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")
    classifier = get_classifying_agent()

    for job in jobs:
        file_path = get_path_to_email(job.email_id)
        email_data = json.loads(file_path.read_text())
        res = await classifier.run(email_data.get('content'))
    
        payload = {"classification" : res.output.model_dump_json()}
        print(payload)

        if not res.output.is_quote:
            update_queued_job(job.id, JobStatus.COMPLETED, json.dumps(payload))
            # file_path.unlink()
            continue
        update_queued_job(job.id, JobStatus.CLASSIFIED, json.dumps(payload))


async def extract_quotations():
    quotation_emails = get_queued_jobs_by_stat(JobStatus.CLASSIFIED)
    print(f"extracting quote from {len(quotation_emails)} emails")
    extractor = get_extractor_agent()

    for job in quotation_emails:
        file_path = get_path_to_email(job.email_id)
        email_data = json.loads(file_path.read_text())
        res = await extractor.run(email_data.get("content"))

        payload = {"extraction": res.output.model_dump_json()}
        print(payload)
        update_queued_job(job.id, JobStatus.EXTRACTED, json.dumps(payload))


async def research_companies():
    jobs = get_queued_jobs_by_stat(JobStatus.EXTRACTED)
    print(f"researching {len(jobs)} companies")
    researcher = get_external_research_agent()

    for job in jobs:
        meta = json.loads(job.meta_data or "{}")
        extraction = json.loads(meta.get("extraction", "{}"))
        company = extraction.get("company")
        if not company:
            continue

        res = await researcher.run(f"Research this company: {company}")
        payload = json.loads(job.meta_data or "{}")
        payload["external_research"] = res.output.model_dump_json()
        print(payload)
        update_queued_job(job.id, JobStatus.RESEARCH_EXT, json.dumps(payload))


async def research_products():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_EXT)
    print(f"researching {len(jobs)} products")
    researcher = get_internal_research_agent()

    for job in jobs:
        meta = json.loads(job.meta_data or "{}")
        extraction = json.loads(meta.get("extraction", "{}"))
        product = extraction.get("product")
        if not product:
            continue

        res = await researcher.run(f"Find this product in the catalog: {product}")
        payload = json.loads(job.meta_data or "{}")
        payload["internal_research"] = res.output.model_dump_json()
        print(payload)
        update_queued_job(job.id, JobStatus.RESEARCH_INT, json.dumps(payload))


async def draft_emails():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_INT)
    print(f"drafting {len(jobs)} emails")
    drafter = get_email_draft_agent()

    for job in jobs:
        meta = json.loads(job.meta_data or "{}")
        research = meta.get("internal_research")
        if not research:
            continue

        res = await drafter.run(
            f"Write a quotation email using this catalog research: {research}"
        )
        payload = json.loads(job.meta_data or "{}")
        payload["draft"] = res.output.model_dump_json()
        print(payload)
        update_queued_job(job.id, JobStatus.DRAFTED, json.dumps(payload))


async def main():
    await classify_emails()
    await extract_quotations()
    await research_companies()
    await research_products()
    await draft_emails()

if __name__ == "__main__":
    asyncio.run(main())

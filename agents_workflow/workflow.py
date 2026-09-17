from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.models.email_retriever_models import JobStatus
from .agents.classifier import get_classifying_agent
from .agents.extractor_agent import get_extractor_agent
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

async def main():
    await classify_emails()
    await extract_quotations()

if __name__ == "__main__":
    asyncio.run(main())

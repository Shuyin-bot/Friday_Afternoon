from db_contexts.repos.email_repository import get_queued_jobs_by_stat
from .agents.classifier import get_classifying_agent, ClassifierOutput
import asyncio
from pydantic_ai.agent import Agent
from pathlib import Path
import json


async def main():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")
    classifier = get_classifying_agent()

    for job in jobs:
        file_path = Path.joinpath(Path.cwd(), "data", "emails", f"{job.email_id}_email.json")
        email_data = json.loads(file_path.read_text())
        res = await classifier.run(email_data.get('content'))
        print(res)
        break


if __name__ == "__main__":
    asyncio.run(main())

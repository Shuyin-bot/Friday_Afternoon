from db_contexts.repos.email_repository import get_queued_jobs_by_stat
from .agents.classifier import Classifier
import asyncio
from .provider.base_provider import model
from pydantic_ai.agent import Agent
from pathlib import Path
import json

async def main():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")
    classifier = Agent(
        model, 
        instructions="You are a classifier, you look at the content of an email and determine if it is a quotation email or not"
    )

    for job in jobs:
        file_path = Path.joinpath(Path.cwd(), "data", "emails", f"{job.email_id}_email.json")
        email_data = json.loads(file_path.read_text())
        await classifier.run(email_data.get('content'))
        

if __name__ == "__main__":
    asyncio.run(main())

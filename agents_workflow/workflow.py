from db_contexts.repos.email_repository import get_queued_jobs_by_stat
import asyncio

async def main():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")

    for job in jobs:
        print(job)

if __name__ == "__main__":
    asyncio.run(main())

from db_contexts.repos.email_repository import get_queued_jobs
import asyncio

async def main():
    jobs = get_queued_jobs()
    print(f"retrieved {len(jobs)}")

if __name__ == "__main__":
    asyncio.run(main())

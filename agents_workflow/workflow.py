from db_contexts.repos.email_repository import get_queued_jobs

if __name__ == "__main__":
    emails = get_queued_jobs()
    print(emails)

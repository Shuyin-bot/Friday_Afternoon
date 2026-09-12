from db_contexts.sessions import SessionLocal
from db_contexts.models import RetrievedEmail, QueuedJob

def create_email_if_not_exist(
    email_id: int,
    from_email: str,
    subject: str,
) -> bool:
    with SessionLocal() as session:
        existing_email = session.query(RetrievedEmail).filter_by(email_id=email_id).first()
        if existing_email:
            return False  # Email already exists

        new_email = RetrievedEmail(
            email_id=email_id,
            from_email=from_email,
            subject=subject,
        )
        session.add(new_email)
        session.flush()

        new_job = QueuedJob(
            email_id=new_email.id,
        )
        session.add(new_job)
        session.commit()
        return True  # New email recorded


def filter_out_seen_emails(email_ids: list) -> list:
    ret = []
    with SessionLocal() as session:
        for id in email_ids:
            email_id = int(id.decode('utf8'))
            existing_email = session.query(RetrievedEmail).filter_by(email_id=email_id).first()
            if existing_email:
                continue
            ret.append(id)
    return ret

from db_contexts.sessions import SessionLocal
from db_contexts.models import RetrievedEmail

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
        session.commit()
        return True  # New email recorded


def does_email_exist(email_id: int) -> bool:
    with SessionLocal() as session:
        existing_email = session.query(RetrievedEmail).filter_by(email_id=email_id).first()
        if existing_email:
            return True
        return False

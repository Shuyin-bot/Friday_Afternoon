from datetime import datetime, timezone

from db_contexts.models import (
    HumanRequest,
    HumanRequestStatus,
    HumanRequestType,
)
from db_contexts.sessions import SessionLocal


def create_human_request(
    queued_job_id: int,
    request_type: HumanRequestType,
    question: str,
    context: dict | None = None,
) -> HumanRequest:
    with SessionLocal() as session:
        request = HumanRequest(
            queued_job_id=queued_job_id,
            request_type=request_type,
            question=question,
            context=context or {},
        )
        session.add(request)
        session.commit()
        return request


def get_human_request(request_id: int) -> HumanRequest | None:
    with SessionLocal() as session:
        return session.query(HumanRequest).filter_by(id=request_id).first()


def get_pending_human_requests() -> list[HumanRequest]:
    with SessionLocal() as session:
        return session.query(HumanRequest).filter_by(
            status=HumanRequestStatus.PENDING
        ).order_by(HumanRequest.created_at).all()


def answer_human_request(
    request_id: int,
    answer: str,
    status: HumanRequestStatus = HumanRequestStatus.ANSWERED,
) -> HumanRequest | None:
    with SessionLocal() as session:
        request = session.query(HumanRequest).filter_by(id=request_id).first()
        if not request:
            return None
        request.answer = answer
        request.status = status
        request.answered_at = datetime.now(timezone.utc)
        session.commit()
        return request

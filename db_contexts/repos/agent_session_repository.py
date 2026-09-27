from datetime import datetime, timezone
import json

from db_contexts.models import AgentSession, AgentSessionStatus, JobStatus, QueuedJob
from db_contexts.sessions import SessionLocal


def create_agent_session(
    queued_job_id: int,
    status: AgentSessionStatus = AgentSessionStatus.ACTIVE,
    current_step: str | None = None,
    summary: dict | None = None,
    context: dict | None = None,
    message_history: list | None = None,
) -> AgentSession:
    with SessionLocal() as session:
        agent_session = AgentSession(
            queued_job_id=queued_job_id,
            status=status,
            current_step=current_step,
            summary=summary or {},
            context=context or {},
            message_history=message_history or [],
        )
        session.add(agent_session)
        session.commit()
        return agent_session


def get_agent_session(session_id: int) -> AgentSession | None:
    with SessionLocal() as session:
        return session.query(AgentSession).filter_by(id=session_id).first()


def get_agent_session_by_job_id(queued_job_id: int) -> AgentSession | None:
    with SessionLocal() as session:
        return session.query(AgentSession).filter_by(
            queued_job_id=queued_job_id
        ).first()


def get_or_create_agent_session(queued_job_id: int) -> AgentSession:
    existing_session = get_agent_session_by_job_id(queued_job_id)
    if existing_session:
        return existing_session
    return create_agent_session(queued_job_id)


def update_agent_session(
    session_id: int,
    status: AgentSessionStatus | None = None,
    current_step: str | None = None,
    summary: dict | None = None,
    context: dict | None = None,
    message_history: list | None = None,
    last_error: str | None = None,
) -> AgentSession | None:
    with SessionLocal() as session:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if not agent_session:
            return None

        if status is not None:
            agent_session.status = status
        if current_step is not None:
            agent_session.current_step = current_step
        if summary is not None:
            agent_session.summary = summary
        if context is not None:
            agent_session.context = context
        if message_history is not None:
            agent_session.message_history = message_history
        if last_error is not None:
            agent_session.last_error = last_error

        agent_session.updated_at = datetime.now(timezone.utc)
        session.commit()
        return agent_session


def append_agent_message(
    session_id: int,
    message: dict,
) -> AgentSession | None:
    with SessionLocal() as session:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if not agent_session:
            return None

        history = list(agent_session.message_history or [])
        history.append(message)
        agent_session.message_history = history
        agent_session.updated_at = datetime.now(timezone.utc)
        session.commit()
        return agent_session


def send_job_back_for_revision(
    queued_job_id: int,
    comment: str,
) -> AgentSession | None:
    """Store reviewer feedback and make the job ready for agent resumption."""
    with SessionLocal() as session:
        agent_session = session.query(AgentSession).filter_by(
            queued_job_id=queued_job_id
        ).first()
        job = session.query(QueuedJob).filter_by(id=queued_job_id).first()
        if not agent_session or not job:
            return None

        try:
            metadata = json.loads(job.meta_data or "{}")
        except json.JSONDecodeError:
            metadata = {}

        metadata["review_action"] = "SENT_BACK_FOR_REVISION"
        metadata["review_comment"] = comment
        metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()

        job.meta_data = json.dumps(metadata)
        job.status = JobStatus.CLASSIFIED
        agent_session.status = AgentSessionStatus.READY_TO_RESUME
        agent_session.current_step = "draft_review_feedback"
        agent_session.summary = {
            **(agent_session.summary or {}),
            "review_feedback": comment,
        }
        agent_session.updated_at = datetime.now(timezone.utc)
        session.commit()
        return agent_session

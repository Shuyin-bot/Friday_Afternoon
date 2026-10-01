"""FastAPI review API for the quotation workflow."""

import json
import asyncio
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from db_contexts.models import JobStatus
from db_contexts.repos.agent_session_repository import send_job_back_for_revision
from db_contexts.repos.email_repository import (
    get_queued_job,
    get_queued_job_counts,
    get_queued_jobs,
    get_queued_jobs_by_stat,
    update_queued_job,
)
from db_contexts.repos.human_request_repository import (
    answer_human_request_and_resume,
    get_answered_human_requests,
    get_human_request,
    get_pending_human_requests,
)
from scripts.seed_mock_leads import count_seeded_leads

from .models import (
    HumanRequestAnswer,
    HumanRequestResponse,
    DraftUpdate,
    DraftReviewComment,
    JobDetail,
    JobSummary,
    RunResponse,
    StatsResponse,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Quotation Bot Review API",
    description="API for reviewing quotation jobs and human-in-the-loop requests.",
    version="0.1.0",
)


def _safe_json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _deep_parse(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _deep_parse(item) for key, item in value.items()}
    if isinstance(value, str):
        parsed = _safe_json(value)
        if isinstance(parsed, (dict, list)):
            return _deep_parse(parsed)
    return value


def _email_json_path(email_id: int) -> Path:
    return REPO_ROOT / "data" / "emails" / f"{email_id}_email.json"


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _to_summary(job) -> JobSummary:
    metadata = _job_metadata(job)
    return JobSummary(
        id=job.id,
        status=_status_value(job.status),
        from_email=job.email.from_email if job.email else "unknown",
        subject=job.email.subject if job.email else "unknown",
        created_at=job.created_at.isoformat(),
        review_action=metadata.get("review_action"),
        reviewed_at=metadata.get("reviewed_at"),
    )


def _to_human_request(request) -> HumanRequestResponse:
    return HumanRequestResponse(
        id=request.id,
        queued_job_id=request.queued_job_id,
        request_type=_status_value(request.request_type),
        question=request.question,
        context=request.context or {},
        status=_status_value(request.status),
        answer=request.answer,
        created_at=request.created_at.isoformat(),
        answered_at=request.answered_at.isoformat() if request.answered_at else None,
    )


@app.get("/api/stats", response_model=StatsResponse, tags=["jobs"])
def get_stats() -> StatsResponse:
    counts = get_queued_job_counts()
    return StatsResponse(counts=counts, total=sum(counts.values()))


@app.get("/api/events", tags=["jobs"])
async def job_events(request: Request) -> StreamingResponse:
    """Stream job-count changes so dashboards update without polling."""
    async def event_stream():
        previous_counts = None
        heartbeat = 0
        while True:
            if await request.is_disconnected():
                break

            counts = get_queued_job_counts()
            if counts != previous_counts:
                payload = json.dumps({"counts": counts, "total": sum(counts.values())})
                yield f"event: job_status\ndata: {payload}\n\n"
                previous_counts = counts
                heartbeat = 0
            elif heartbeat >= 15:
                yield ": heartbeat\n\n"
                heartbeat = 0

            await asyncio.sleep(2)
            heartbeat += 2

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/jobs", response_model=list[JobSummary], tags=["jobs"])
def list_jobs(status: str | None = None) -> list[JobSummary]:
    if status:
        try:
            jobs = get_queued_jobs_by_stat(JobStatus(status))
        except ValueError:
            raise HTTPException(400, f"Unknown status: {status}")
    else:
        jobs = get_queued_jobs()
    return [_to_summary(job) for job in jobs]


@app.get("/api/jobs/{job_id}", response_model=JobDetail, tags=["jobs"])
def get_job(job_id: int) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    email_body = None
    if job.email:
        path = _email_json_path(job.email.email_id)
        if path.exists():
            email_body = json.loads(path.read_text()).get("content")

    summary = _to_summary(job)
    return JobDetail(
        **summary.model_dump(),
        email_body=email_body,
        meta_data=_deep_parse(_safe_json(job.meta_data) or {}),
    )


@app.post("/api/jobs/{job_id}/approve", response_model=JobDetail, tags=["jobs"])
def approve_job(job_id: int) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DRAFTED:
        raise HTTPException(400, "Only drafted quotation jobs can be approved")
    metadata = _job_metadata(job)
    metadata["review_action"] = "APPROVED"
    metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    update_queued_job(job_id, JobStatus.COMPLETED, json.dumps(metadata))
    return get_job(job_id)


@app.post("/api/jobs/{job_id}/unapprove", response_model=JobDetail, tags=["jobs"])
def unapprove_job(job_id: int) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(400, "Only approved quotation jobs can be unapproved")

    metadata = _job_metadata(job)
    if metadata.get("review_action") != "APPROVED":
        raise HTTPException(400, "Only approved quotation jobs can be unapproved")
    metadata["review_action"] = "UNAPPROVED"
    metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    update_queued_job(job_id, JobStatus.DRAFTED, json.dumps(metadata))
    return get_job(job_id)


def _job_metadata(job) -> dict[str, Any]:
    try:
        return json.loads(job.meta_data or "{}")
    except json.JSONDecodeError:
        return {}


@app.put("/api/jobs/{job_id}/draft", response_model=JobDetail, tags=["jobs"])
def update_draft(job_id: int, payload: DraftUpdate) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DRAFTED:
        raise HTTPException(400, "Only drafted quotation jobs can be edited")

    metadata = _job_metadata(job)
    metadata["draft"] = payload.model_dump()
    metadata["review_action"] = "EDITED"
    metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    update_queued_job(job_id, JobStatus.DRAFTED, json.dumps(metadata))
    return get_job(job_id)


@app.post("/api/jobs/{job_id}/reject", response_model=JobDetail, tags=["jobs"])
def reject_draft(job_id: int) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DRAFTED:
        raise HTTPException(400, "Only drafted quotation jobs can be rejected")

    metadata = _job_metadata(job)
    metadata.pop("draft", None)
    metadata["review_action"] = "REJECTED"
    metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    update_queued_job(job_id, JobStatus.COMPLETED, json.dumps(metadata))
    return get_job(job_id)


@app.post(
    "/api/jobs/{job_id}/review-comment",
    response_model=JobDetail,
    tags=["jobs"],
)
def send_draft_back_for_revision(
    job_id: int,
    payload: DraftReviewComment,
) -> JobDetail:
    job = get_queued_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DRAFTED:
        raise HTTPException(400, "Only drafted quotation jobs can receive review feedback")
    if not payload.comment.strip():
        raise HTTPException(400, "Review comment cannot be empty")

    session = send_job_back_for_revision(job_id, payload.comment.strip())
    if not session:
        raise HTTPException(400, "No agent session exists for this job")
    return get_job(job_id)


@app.get(
    "/api/human-requests",
    response_model=list[HumanRequestResponse],
    tags=["human review"],
)
def list_human_requests() -> list[HumanRequestResponse]:
    return [_to_human_request(item) for item in get_pending_human_requests()]


@app.get(
    "/api/human-requests/history",
    response_model=list[HumanRequestResponse],
    tags=["human review"],
)
def list_human_request_history() -> list[HumanRequestResponse]:
    return [_to_human_request(item) for item in get_answered_human_requests()]


@app.get(
    "/api/human-requests/{request_id}",
    response_model=HumanRequestResponse,
    tags=["human review"],
)
def get_human_request_detail(request_id: int) -> HumanRequestResponse:
    request = get_human_request(request_id)
    if not request:
        raise HTTPException(404, "Human request not found")
    return _to_human_request(request)


@app.post(
    "/api/human-requests/{request_id}/answer",
    response_model=HumanRequestResponse,
    tags=["human review"],
)
def answer_request(
    request_id: int,
    payload: HumanRequestAnswer,
) -> HumanRequestResponse:
    # This repository operation answers the request and, in the same
    # transaction, marks the session ready and requeues the job as CLASSIFIED.
    request = answer_human_request_and_resume(request_id, payload.answer)
    if not request:
        raise HTTPException(404, "Human request not found")
    return _to_human_request(request)


def _run_module(module: str) -> None:
    subprocess.run([sys.executable, "-m", module], cwd=REPO_ROOT, check=False)


def _run_retrieve_and_seed_missing_mocks() -> None:
    _run_module("email_retriever.retriever")
    if count_seeded_leads() == 0:
        _run_module("scripts.seed_mock_leads")


@app.post("/api/run/retrieve", response_model=RunResponse, tags=["actions"])
def run_retrieve(background_tasks: BackgroundTasks) -> RunResponse:
    background_tasks.add_task(_run_retrieve_and_seed_missing_mocks)
    return RunResponse(
        started=True,
        message=(
            "IMAP retrieval started; missing mock leads will be seeded automatically."
        ),
    )


@app.post("/api/run/workflow", response_model=RunResponse, tags=["actions"])
def run_workflow(background_tasks: BackgroundTasks) -> RunResponse:
    background_tasks.add_task(_run_module, "agents_workflow.workflow")
    return RunResponse(started=True, message="Workflow started in the background.")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

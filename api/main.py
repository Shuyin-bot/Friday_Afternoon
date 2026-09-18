"""Read-mostly review API for the quotation-bot pipeline.

Exposes the queued_jobs / retrieved_email tables as JSON so a human can
review what the agent workflow produced, and lets the reviewer trigger the
retriever and the workflow from the browser instead of a terminal.

Run with:
    uv run uvicorn api.main:app --reload --port 8000

- Swagger / OpenAPI docs: http://localhost:8000/docs
- Single-page dashboard:  http://localhost:8000/
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db_contexts import SessionLocal
from db_contexts.models.email_retriever_models import JobStatus, QueuedJob, RetrievedEmail

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Quotation Bot Review API",
    description=(
        "Read-only view into the email -> agent workflow pipeline, plus "
        "two buttons to trigger the retriever and the workflow. Not a "
        "public API: no auth, intended for local/dev review only."
    ),
    version="0.1.0",
)


def _safe_json(value: str | None) -> Any:
    """Best-effort JSON decode. Returns the raw string if it is not JSON."""
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _deep_parse(value: Any) -> Any:
    """Recursively decode JSON-encoded strings.

    Agent outputs are stored via `model_dump_json()`, so `meta_data` is a
    JSON object whose values are themselves JSON strings. This unwraps that
    one extra layer so the API returns real nested objects, not escaped
    strings, for both /docs and the dashboard.
    """
    if isinstance(value, dict):
        return {k: _deep_parse(v) for k, v in value.items()}
    if isinstance(value, str):
        parsed = _safe_json(value)
        if isinstance(parsed, (dict, list)):
            return _deep_parse(parsed)
        return value
    return value


class JobSummary(BaseModel):
    id: int
    status: str
    from_email: str
    subject: str
    created_at: str


class JobDetail(JobSummary):
    email_body: str | None = None
    meta_data: dict | None = None


class StatsResponse(BaseModel):
    counts: dict[str, int]
    total: int


class RunResponse(BaseModel):
    started: bool
    message: str


def _email_json_path(retrieved_email: RetrievedEmail) -> Path:
    return REPO_ROOT / "data" / "emails" / f"{retrieved_email.email_id}_email.json"


def _to_summary(job: QueuedJob) -> JobSummary:
    return JobSummary(
        id=job.id,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        from_email=job.email.from_email if job.email else "unknown",
        subject=job.email.subject if job.email else "unknown",
        created_at=job.created_at.isoformat(),
    )


@app.get("/api/stats", response_model=StatsResponse, tags=["jobs"])
def get_stats() -> StatsResponse:
    """Count queued jobs by pipeline status, e.g. PENDING/CLASSIFIED/DRAFTED."""
    with SessionLocal() as session:
        jobs = session.query(QueuedJob).all()
        counts: dict[str, int] = {status.value: 0 for status in JobStatus}
        for job in jobs:
            key = job.status.value if hasattr(job.status, "value") else str(job.status)
            counts[key] = counts.get(key, 0) + 1
        return StatsResponse(counts=counts, total=len(jobs))


@app.get("/api/jobs", response_model=list[JobSummary], tags=["jobs"])
def list_jobs(status: str | None = None) -> list[JobSummary]:
    """List queued jobs, optionally filtered by status (e.g. ?status=DRAFTED)."""
    with SessionLocal() as session:
        query = session.query(QueuedJob)
        if status:
            try:
                query = query.filter_by(status=JobStatus(status))
            except ValueError:
                raise HTTPException(400, f"Unknown status: {status}")
        jobs = query.order_by(QueuedJob.id).all()
        return [_to_summary(job) for job in jobs]


@app.get("/api/jobs/{job_id}", response_model=JobDetail, tags=["jobs"])
def get_job(job_id: int) -> JobDetail:
    """Full detail for one job: original email body plus every pipeline stage."""
    with SessionLocal() as session:
        job = session.query(QueuedJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")

        email_body = None
        if job.email:
            path = _email_json_path(job.email)
            if path.exists():
                email_body = json.loads(path.read_text()).get("content")

        meta = _deep_parse(_safe_json(job.meta_data) or {})

        summary = _to_summary(job)
        return JobDetail(**summary.model_dump(), email_body=email_body, meta_data=meta)


def _run_module(module: str) -> None:
    subprocess.run(
        [sys.executable, "-m", module],
        cwd=REPO_ROOT,
        check=False,
    )


@app.post("/api/run/retrieve", response_model=RunResponse, tags=["actions"])
def run_retrieve(background_tasks: BackgroundTasks) -> RunResponse:
    """Trigger `email_retriever.retriever` in the background (IMAP fetch)."""
    background_tasks.add_task(_run_module, "email_retriever.retriever")
    return RunResponse(started=True, message="Retriever started in the background.")


@app.post("/api/run/workflow", response_model=RunResponse, tags=["actions"])
def run_workflow(background_tasks: BackgroundTasks) -> RunResponse:
    """Trigger `agents_workflow.workflow` in the background (runs all 5 agent stages)."""
    background_tasks.add_task(_run_module, "agents_workflow.workflow")
    return RunResponse(started=True, message="Workflow started in the background.")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

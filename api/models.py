from pydantic import BaseModel


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


class HumanRequestAnswer(BaseModel):
    answer: str


class DraftUpdate(BaseModel):
    subject: str
    body: str


class HumanRequestResponse(BaseModel):
    id: int
    queued_job_id: int
    request_type: str
    question: str
    context: dict
    status: str
    answer: str | None = None
    created_at: str
    answered_at: str | None = None

from pydantic_ai import RunContext

from db_contexts.models import HumanRequestType
from db_contexts.repos.human_request_repository import create_human_request

from .tool_logger import log_tool_use


class HumanInputRequired(Exception):
    """Signal that the workflow must pause for a human response."""

    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(f"Human input required for request {request_id}")


def request_human_input(
    ctx: RunContext[int],
    question: str,
    request_type: HumanRequestType = HumanRequestType.CLARIFICATION,
    context: dict[str, str] | None = None,
) -> None:
    """Create a human request and pause the current workflow job."""
    log_tool_use("request_human_input", f"type={request_type.value}")
    request = create_human_request(
        queued_job_id=ctx.deps,
        request_type=request_type,
        question=question,
        context=context,
    )
    raise HumanInputRequired(request.id)

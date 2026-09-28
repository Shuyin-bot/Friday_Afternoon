from pydantic_ai import RunContext

from db_contexts.models import AgentSessionStatus, HumanRequestType
from db_contexts.repos.agent_session_repository import update_agent_session
from db_contexts.repos.human_request_repository import create_human_request

from ..core_models import CoreAgentDependencies
from ..session_history import serialize_message_history
from .tool_logger import log_tool_use


def request_human_input(
    ctx: RunContext[CoreAgentDependencies],
    question: str,
    request_type: HumanRequestType = HumanRequestType.CLARIFICATION,
    context: dict[str, str] | None = None,
) -> None:
    """Create a human request and pause the current workflow job."""
    log_tool_use("request_human_input", f"type={request_type.value}")
    request = create_human_request(
        queued_job_id=ctx.deps.job_id,
        request_type=request_type,
        question=question,
        context=context,
    )
    update_agent_session(
        session_id=ctx.deps.session_id,
        status=AgentSessionStatus.WAITING_FOR_HUMAN,
        current_step="human_input",
        summary={
            **ctx.deps.session_summary,
            "human_request_id": request.id,
            "last_question": question,
            "request_type": request_type.value,
        },
        message_history=serialize_message_history(ctx.messages),
    )
    # Let PydanticAI close the interrupted tool call in the message history.
    # This makes the history valid for a later resumed run.
    ctx.cancel()

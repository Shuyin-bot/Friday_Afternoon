import json
from typing import Sequence

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart


def load_message_history(history: list | None) -> list[ModelMessage]:
    """Deserialize and repair a stored PydanticAI message history."""
    messages = ModelMessagesTypeAdapter.validate_python(history or [])
    return repair_message_history(messages)


def serialize_message_history(messages: Sequence[ModelMessage]) -> list[dict]:
    """Serialize PydanticAI messages into JSON-compatible dictionaries."""
    repaired_messages = repair_message_history(list(messages))
    return json.loads(ModelMessagesTypeAdapter.dump_json(repaired_messages).decode())


def repair_message_history(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Close tool calls that have no tool-return message.

    A human-input tool can interrupt a model response that contains several
    parallel tool calls. PydanticAI may leave that call without a return part,
    which prevents a later run from accepting a new prompt.
    """
    tool_calls = {}
    completed_calls = set()

    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call":
                tool_calls[part.tool_call_id] = part.tool_name
            elif part.part_kind == "tool-return":
                completed_calls.add(part.tool_call_id)

    missing_calls = [
        (tool_call_id, tool_name)
        for tool_call_id, tool_name in tool_calls.items()
        if tool_call_id not in completed_calls
    ]
    if not missing_calls:
        return messages

    messages.append(
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name=tool_name,
                    tool_call_id=tool_call_id,
                    content="This tool call was interrupted while waiting for human review.",
                    outcome="interrupted",
                )
                for tool_call_id, tool_name in missing_calls
            ]
        )
    )
    return messages

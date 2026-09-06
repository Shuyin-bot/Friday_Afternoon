"""Validated execution runner for Python agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ValidationError

from .models import AgentContext, AgentExecutionRecord
from .registry import AgentRegistry
from .runs import AgentRunStore


class AgentExecutionError(RuntimeError):
    """Raised when an agent fails or returns invalid output."""


class AgentRunner:
    """Validate inputs, execute registered agents, validate outputs, and audit runs."""

    def __init__(self, registry: AgentRegistry, run_store: AgentRunStore):
        """Create a runner with an agent registry and execution recorder."""
        self.registry = registry
        self.run_store = run_store

    async def run(
        self,
        agent_name: str,
        context: AgentContext,
    ) -> BaseModel:
        """Run one agent with typed input/output validation and audit persistence."""
        agent = self.registry.get(agent_name)
        started = datetime.now(timezone.utc)
        record = AgentExecutionRecord(
            job_id=context.job.id,
            agent_name=agent_name,
            status="RUNNING",
            started_at=started,
        )
        self.run_store.save(record)

        try:
            validated_input: Any = agent.input_model.model_validate(context.input_data)
            validated_context = context.model_copy(update={"input_data": validated_input.model_dump()})
            raw_output = await agent.run(validated_context)
            output = agent.output_model.model_validate(raw_output)
        except (ValidationError, TypeError, ValueError) as error:
            self._save_failure(record, error)
            raise AgentExecutionError(f"Agent {agent_name} returned invalid data: {error}") from error
        except Exception as error:
            self._save_failure(record, error)
            raise AgentExecutionError(f"Agent {agent_name} failed: {error}") from error

        completed = record.model_copy(
            update={
                "status": "COMPLETED",
                "finished_at": datetime.now(timezone.utc),
                "output": output.model_dump(),
            }
        )
        self.run_store.save(completed)
        return output

    def _save_failure(self, record: AgentExecutionRecord, error: Exception) -> None:
        """Persist a failed run before propagating the execution error."""
        self.run_store.save(
            record.model_copy(
                update={
                    "status": "FAILED",
                    "finished_at": datetime.now(timezone.utc),
                    "error": str(error),
                }
            )
        )

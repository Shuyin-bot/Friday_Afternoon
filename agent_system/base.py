"""Interfaces for Python-defined agents."""

from __future__ import annotations

from typing import Protocol, Type

from pydantic import BaseModel

from .models import AgentContext, AgentMetadata


class BaseAgent(Protocol):
    """Contract implemented by every agent in the framework."""

    metadata: AgentMetadata
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]

    async def run(self, context: AgentContext) -> BaseModel:
        """Execute the agent using validated context and return typed output."""

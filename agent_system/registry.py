"""Registry for explicitly available Python agents."""

from __future__ import annotations

from .base import BaseAgent


class AgentNotFoundError(KeyError):
    """Raised when a requested agent is not registered."""


class AgentRegistry:
    """Map stable agent names to agent implementations."""

    def __init__(self, agents: list[BaseAgent] | None = None):
        """Create a registry with optional initial agents."""
        self._agents = {}
        for agent in agents or []:
            self.register(agent)

    def register(self, agent: BaseAgent) -> None:
        """Register an agent by its declared metadata name."""
        name = agent.metadata.name
        if name in self._agents:
            raise ValueError(f"Agent {name!r} is already registered")
        self._agents[name] = agent

    def get(self, name: str) -> BaseAgent:
        """Return a registered agent or raise an explicit lookup error."""
        try:
            return self._agents[name]
        except KeyError as error:
            raise AgentNotFoundError(name) from error

    def names(self) -> tuple[str, ...]:
        """Return registered agent names in registration order."""
        return tuple(self._agents)

from typing import Any
from .base_agent import CustomBaseAgent
from pydantic_ai import Agent
from db_contexts import QueuedJob, JobStatus

class Classifier(CustomBaseAgent, Agent):

    def __init__(
        self, 
        model: str, 
        system_prompt: str, 
        input_payload: QueuedJob, 
        **kwargs: Any
    ):
        self.m_system_prompt = system_prompt
        self.input_payload = input_payload
        super().__init__(model=model, **kwargs)
    
    def _setup_tools(self):
        @self.system_prompt
        def add_context() -> str:
            return self.m_system_prompt

    def run(self, user_prompt: str) -> None:
        self.input_payload.status
        pass
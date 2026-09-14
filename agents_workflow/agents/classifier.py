from typing import Any
from .base_agent import CustomBaseAgent
from pydantic_ai import Agent
from db_contexts import QueuedJob, JobStatus

class Classifier(Agent):

    def __init__(
        self, 
        **kwargs: Any
    ):
        # self.m_system_prompt = system_prompt
        super().__init__(**kwargs)
    
    def _setup_tools(self):
        @self.system_prompt
        def add_context() -> str:
            return self.m_system_prompt

    def run(self, user_prompt: str) -> None:
        self.input_payload.status
        pass
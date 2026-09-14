from abc import ABC
from typing import Any
from db_contexts import QueuedJob


class CustomBaseAgent(ABC):

    def __init__(self, system_prompt: str):
        self.m_system_prompt = system_prompt

    def run(self) -> None:
        pass
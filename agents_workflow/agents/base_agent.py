from abc import ABC
from typing import Any


class CustomBaseAgent(ABC):

    def __init__(self, system_prompt: str):
        self.m_system_prompt = system_prompt
        self.input_payload: dict[str, Any] = None

    def run(self) -> None:
        pass
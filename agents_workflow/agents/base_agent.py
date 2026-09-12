from abc import ABC

class AgentBase(ABC):

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def run(self) -> None:
        pass
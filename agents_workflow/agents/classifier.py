from .base_agent import AgentBase

class Classifier(AgentBase):

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
    
    def run(self):
        pass
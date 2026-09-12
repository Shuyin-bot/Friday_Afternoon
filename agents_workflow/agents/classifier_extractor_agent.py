from .base_agent import AgentBase

class ClassifierAndExtractor(AgentBase):

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
    
    def run(self):
        pass
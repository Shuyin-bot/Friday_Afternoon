from typing import Any
from pydantic_ai import Agent
from db_contexts import QueuedJob, JobStatus
from pydantic import BaseModel, Field
from ..provider.base_provider import model


class ClassifierOutput(BaseModel):
    result: float = Field(ge=0.0, le=1.0)
    reason: str
    is_quote: bool


def get_classifying_agent() -> Agent:
    classifier = Agent(
        model, 
        instructions="You are a classifier, you look at the content of an email and determine if it is a quotation email or not",
        output_type=ClassifierOutput
    )
    return classifier

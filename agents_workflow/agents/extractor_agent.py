from typing import Any
from pydantic_ai import Agent
from db_contexts import QueuedJob, JobStatus
from pydantic import BaseModel, Field
from ..provider.base_provider import model

class ExtractorOutput(BaseModel):
    product: str
    quantity: int
    other: str
    company: str | None
    contact_person: str | None


def get_extractor_agent() -> Agent:
    extractor = Agent(
        model,
        instructions="Your role is to extract an quotation info found in the email, like product, the amount of product requested etc",
        output_type=ExtractorOutput
    )
    return extractor
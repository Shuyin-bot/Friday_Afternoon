from pydantic_ai import Agent
from pydantic import BaseModel
from ..provider.base_provider import model


class ExtractorOutput(BaseModel):
    product: str | None = None
    quantity: int | None = None
    other: str | None = None
    company: str | None = None
    contact_person: str | None = None


def get_extractor_agent() -> Agent:
    extractor = Agent(
        model,
        instructions=(
            "Your role is to extract quotation information from an email. "
            "Extract the requested product, quantity, company, contact person, "
            "and any other relevant requirements. If information is missing, "
            "return None instead of guessing."
        ),
        output_type=ExtractorOutput
    )
    return extractor

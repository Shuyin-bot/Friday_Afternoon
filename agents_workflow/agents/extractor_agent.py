from pydantic_ai import Agent
from pydantic import BaseModel, Field
from ..provider.base_provider import model


class ExtractorOutput(BaseModel):
    products: list[str] = Field(default_factory=list)
    quantity: int | None = None
    other: str | None = None
    company: str | None = None
    contact_person: str | None = None


def get_extractor_agent() -> Agent:
    extractor = Agent(
        model,
        instructions=(
            "Your role is to extract quotation information from an email. "
            "Extract every distinct product or machine the sender is asking "
            "about into the `products` list, as separate entries. For example, "
            "a request for 'a case erector and a carton sealer' is TWO entries "
            "in `products`, not one combined phrase. If only one item is "
            "requested, return a single-element list. If no specific product "
            "is mentioned, return an empty list instead of guessing. Also "
            "extract quantity, company, contact person, and any other "
            "relevant requirements. If information is missing, return None "
            "instead of guessing."
        ),
        output_type=ExtractorOutput
    )
    return extractor

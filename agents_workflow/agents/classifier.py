from pydantic_ai import Agent
from pydantic import BaseModel
from ..provider.base_provider import model


class ClassifierOutput(BaseModel):
    reason: str
    is_quote: bool


def get_classifying_agent() -> Agent:
    classifier = Agent(
        model,
        instructions=(
            "Your role is to classify an email and determine whether it is a "
            "quotation request. Set is_quote to True only when the sender is "
            "requesting a price, quote, offer, or quotation for a product or "
            "service. Set it to False for unrelated emails. Give a short "
            "reason based only on the email content."
        ),
        output_type=ClassifierOutput
    )
    return classifier

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
            "quotation request. Set is_quote to True when the sender is "
            "requesting a price, quote, offer, or quotation for a product or "
            "service — including RFQ-style buying inquiries that describe "
            "technical specifications and/or budget and ask to schedule a "
            "call, discuss sourcing, or indicate lead times, even if they "
            "never use the literal words 'price' or 'quote'. The underlying "
            "question is: is this sender trying to buy something from us? "
            "Set it to False for unrelated emails (spam, phishing, "
            "recruiting, sponsorship, press, unsolicited supplier pitches, "
            "misrouted invoices, etc.). Give a short reason based only on "
            "the email content."
        ),
        output_type=ClassifierOutput
    )
    return classifier

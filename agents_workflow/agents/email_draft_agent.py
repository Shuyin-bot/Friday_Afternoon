from pydantic import BaseModel
from pydantic_ai import Agent

from ..provider.base_provider import model


class EmailDraftOutput(BaseModel):
    subject: str
    body: str


def get_email_draft_agent() -> Agent:
    drafter = Agent(
        model,
        instructions=(
            "Your role is to draft a quotation reply email using the catalog "
            "research result. Use only the product name, SKU, category, and "
            "other details provided. If the product was found, confirm it and "
            "describe it briefly. If it was not found, say so politely and ask "
            "for more detail. Do not invent prices, stock, or delivery dates."
        ),
        output_type=EmailDraftOutput,
    )
    return drafter

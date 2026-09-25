from pydantic_ai import Agent

from ..provider.base_provider import model
from .tools import (
    calculate_quotation_price_tool,
    draft_quotation_email_tool,
    email_data_extraction_tool,
    external_company_research_tool,
    product_catalog_search_tool,
)


def get_core_agent():
    return Agent(
        model,
        instructions=(
            "Your role is to draft a quotation reply from an inbound email. "
            "Use the tools when necessary to extract request details, search "
            "the catalog, research missing company facts, calculate prices, "
            "and draft the reply. Do not invent products, prices, stock, or "
            "company facts. If information is missing, leave it missing and "
            "say so in the draft."
        ),
        tools=[
            draft_quotation_email_tool,
            calculate_quotation_price_tool,
            email_data_extraction_tool,
            product_catalog_search_tool,
            external_company_research_tool,
        ],
    )

from pydantic_ai import Agent

from ..provider.base_provider import model
from .core_models import CoreAgentDependencies, QuotationDraftOutput
from .email_draft_agent import _seller_context
from .tools import (
    calculate_quotation_price_tool,
    company_research_search_tool,
    company_research_write_tool,
    draft_quotation_email_tool,
    email_data_extraction_tool,
    external_company_research_tool,
    request_human_input,
    product_catalog_search_tool,
)


def get_core_agent():
    return Agent(
        model,
        deps_type=CoreAgentDependencies,
        instructions=(
            _seller_context() + "\n\n"
            "Your role is to draft a quotation reply from an inbound email. "
            "Use the tools when necessary to extract request details, search "
            "the catalog, search stored company research before using external "
            "research, save new company research when it is gathered, calculate "
            "prices, and draft the reply. Do not invent products, prices, stock, "
            "or company facts. If information is missing, leave it missing and "
            "say so in the draft. If a clarification, product choice, price "
            "confirmation, or approval is required, use request_human_input "
            "and do not continue. After using the necessary tools, return the "
            "completed quotation as the final subject and body output. "
            "Always sign the final email with the seller contact from the company "
            "profile. Never use placeholders such as [Your Name], [Your Position], "
            "[Company Name], [Contact Details], or a generic Quotation Team signature."
        ),
        output_type=QuotationDraftOutput,
        tools=[
            draft_quotation_email_tool,
            calculate_quotation_price_tool,
            company_research_search_tool,
            company_research_write_tool,
            email_data_extraction_tool,
            product_catalog_search_tool,
            external_company_research_tool,
            request_human_input,
        ],
    )

from db_contexts.repos.company_research_repository import (
    get_company_research,
    get_company_research_by_name,
    search_company_research,
)
from vector_contexts import search_company_research_semantic

from ..core_models import CompanyResearchOutput, CompanyResearchSearchOutput
from .tool_logger import log_tool_use


def _to_output(research) -> CompanyResearchOutput:
    return CompanyResearchOutput(
        company=research.company,
        summary=research.summary,
        website=research.website,
        industry=research.industry,
        company_size=research.company_size,
        sources=research.sources or [],
    )


def company_research_search_tool(company_name: str) -> CompanyResearchSearchOutput:
    """Search stored company research before using external web research."""
    log_tool_use("company_research_search_tool", "company provided")
    matches = get_company_research_by_name(company_name)
    source = "sql"

    if not matches:
        matches = search_company_research(company_name)

    if not matches:
        source = "semantic"
        matches = []
        for research_id in search_company_research_semantic(company_name):
            if research := get_company_research(int(research_id)):
                matches.append(research)

    return CompanyResearchSearchOutput(
        search_term=company_name,
        found=bool(matches),
        source=source,
        companies=[_to_output(research) for research in matches],
    )

import json

from ..core_models import CompanyResearchOutput
from ..external_research_agent import research_company_online
from .tool_logger import log_tool_use


def external_company_research_tool(company_name: str) -> CompanyResearchOutput:
    """Research a company's public presence on the internet."""
    log_tool_use("external_company_research_tool", "company provided")
    results = json.loads(research_company_online(company_name))
    sources = [item["url"] for item in results if item.get("url")]
    summary = " ".join(item["content"] for item in results if item.get("content"))
    return CompanyResearchOutput(
        company=company_name,
        summary=summary or None,
        website=sources[0] if sources else None,
        sources=sources,
    )

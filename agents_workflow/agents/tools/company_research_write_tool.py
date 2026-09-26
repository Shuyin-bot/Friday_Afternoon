from db_contexts.repos.company_research_repository import create_company_research
from vector_contexts import get_company_research_collection

from ..core_models import CompanyResearchOutput, CompanyResearchWriteOutput
from .tool_logger import log_tool_use


def company_research_write_tool(
    research: CompanyResearchOutput,
) -> CompanyResearchWriteOutput:
    """Save company research in SQLite and the Chroma memory collection."""
    log_tool_use("company_research_write_tool", "research provided")
    saved = create_company_research(
        company=research.company,
        summary=research.summary,
        website=research.website,
        industry=research.industry,
        company_size=research.company_size,
        sources=research.sources,
    )

    document = " ".join(
        value for value in (
            saved.company,
            saved.summary,
            saved.website,
            saved.industry,
            saved.company_size,
        ) if value
    )
    metadata = {
        "research_id": str(saved.id),
        "company": saved.company,
    }
    if saved.industry:
        metadata["industry"] = saved.industry
    get_company_research_collection().upsert(
        ids=[str(saved.id)],
        documents=[document],
        metadatas=[metadata],
    )

    return CompanyResearchWriteOutput(
        saved=True,
        research_id=saved.id,
        company=saved.company,
    )

from db_contexts.models import CompanyResearch
from db_contexts.sessions import SessionLocal
from sqlalchemy import func, or_


def create_company_research(
    company: str,
    summary: str | None = None,
    website: str | None = None,
    industry: str | None = None,
    company_size: str | None = None,
    sources: list[str] | None = None,
) -> CompanyResearch:
    with SessionLocal() as session:
        research = CompanyResearch(
            company=company,
            summary=summary,
            website=website,
            industry=industry,
            company_size=company_size,
            sources=sources or [],
        )
        session.add(research)
        session.commit()
        return research


def get_company_research(research_id: int) -> CompanyResearch | None:
    with SessionLocal() as session:
        return session.query(CompanyResearch).filter_by(id=research_id).first()


def get_company_research_by_name(company: str) -> list[CompanyResearch]:
    with SessionLocal() as session:
        return session.query(CompanyResearch).filter(
            func.lower(CompanyResearch.company) == company.strip().lower()
        ).order_by(CompanyResearch.researched_at.desc()).all()


def search_company_research(search_term: str) -> list[CompanyResearch]:
    term = f"%{search_term.strip()}%"
    with SessionLocal() as session:
        return session.query(CompanyResearch).filter(
            or_(
                CompanyResearch.company.ilike(term),
                CompanyResearch.summary.ilike(term),
                CompanyResearch.website.ilike(term),
                CompanyResearch.industry.ilike(term),
                CompanyResearch.company_size.ilike(term),
            )
        ).order_by(CompanyResearch.researched_at.desc()).all()

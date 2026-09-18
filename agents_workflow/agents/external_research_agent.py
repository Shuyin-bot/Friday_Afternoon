import json
import os

from pydantic import BaseModel
from pydantic_ai import Agent
from tavily import TavilyClient

from ..provider.base_provider import model


class ExternalResearchOutput(BaseModel):
    company: str | None = None
    summary: str | None = None
    website: str | None = None
    industry: str | None = None
    sources: list[str] | None = None


def research_company_online(company: str) -> str:
    """Search the internet for a company's public presence."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise Exception("TAVILY_API_KEY is missing")

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=f"{company} company official website about",
        max_results=5,
    )
    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
        })
    return json.dumps(results)


def get_external_research_agent() -> Agent:
    researcher = Agent(
        model,
        instructions=(
            "Your role is to research a company's public presence on the internet. "
            "Use the research_company_online tool with the company name. "
            "Summarize what the company does, its website, and industry. "
            "If information is missing, return None instead of guessing."
        ),
        output_type=ExternalResearchOutput,
        tools=[research_company_online],
    )
    return researcher

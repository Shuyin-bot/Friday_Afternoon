from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, RunContext
from tavily import TavilyClient, AsyncTavilyClient
from typing import Any, Protocol
from models import AgentMetadata, AgentRiskLevel, AgentContext
from classifier import EmailClassificationInput
from dotenv import load_dotenv
import os 
from llm import LLMSettings, create_model
import asyncio
import json

load_dotenv()
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
client = AsyncTavilyClient(TAVILY_API_KEY)

async def search_web(query: str):
    search_results = await client.search(query)
    urls = [r["url"] for r in search_results["results"]]
    extracted = await client.extract(urls)
    return extracted


RESEARCH_INSTRUCTIONS = """You evaluate the seriousness of a quotation request by checking the web presence of the requesting company."""

class PydanticAIRun(Protocol):
    """Minimal result interface returned by a PydanticAI agent run."""

    output: Any


class PydanticAIClient(Protocol):
    """Subset of the PydanticAI Agent API needed by this agent."""

    async def run(self, user_prompt: str) -> PydanticAIRun:
        """Run the model with one untrusted email prompt."""


class CompanyCredibility(BaseModel):
    """Typed classification result consumed by the next workflow stage."""

    model_config = ConfigDict(frozen=True)

    Serious_request: bool
    confidence: float = Field(ge=0, le=1)
    reason: str
    security_flags: list[str] = Field(default_factory=list)

class Company_To_Cred(BaseModel):
        model_config = ConfigDict(frozen=True)
        comopany_name: str


class PydanticAICompanyCredreviewer:
    """Evaluates seriosity of Quotations by Webpresence of Customers
      collected and evaluated by Ollama."""


    metadata = AgentMetadata(
        name="company_cred_reviewer",
        allowed_tools=("search_web",),
        retry_limit=1,
        risk_level=AgentRiskLevel.LOW,
    )
    input_model = Company_To_Cred
    output_model = CompanyCredibility

    def __init__(self, model: object | None = None,settings: LLMSettings | None = None, client: PydanticAIClient | None = None,
    ):
        """Create the agent, optionally injecting a model or test client."""
        if client is not None:
            self._client = client
        else:
            self._client = Agent(
                model or create_model(settings),
                output_type=CompanyCredibility,
                instructions=RESEARCH_INSTRUCTIONS,
                retries=0,
            )
            self._client.tool_plain(search_web)



    async def run(self, company) -> CompanyCredibility:
        """Run classification and return the PydanticAI structured output."""
        prompt = self._build_prompt(company)
        result = await self._client.run(prompt)
        return result.output

    def _build_prompt(self, Company: str) -> str:
        """Instructions for the AI how to evaluate the company's credibility."""
        return (
            f"Evaluate the seriousness of. the requesting {Company}\n"
            "Use a Point System for exisitng Website, Google Entry, registration in a company, and other relevant information.\n" \
            "Provide a score between 0 and 1, where 1 is a serious request and 0 is not serious.\n"
            "Use the provided Tools to search the web for information about the company and its credibility. tell if u didnt used it \n"
            
        )
def company_name():
    with open('daten.json', 'r', encoding='utf-8') as datei:
    # Daten einlesen und in ein Python-Dictionary konvertieren
        daten = json.load(datei)    
        email = daten["sender"]
        return (email.split(".")[-2])

async def do_something():
    research_agent = PydanticAICompanyCredreviewer()
    data  = await research_agent.run(company_name())
    print(data)

asyncio.run(do_something())
    
import json
from pathlib import Path

from pydantic import BaseModel
from pydantic_ai import Agent

from ..provider.base_provider import model

# repo_root/mock_data/company_info.json — a copy of the frozen
# mock_data/seller/company_info.json fixture, kept inside this project so
# the draft agent knows who it is writing on behalf of (name, value
# propositions, delivery/payment terms). See mock_data/FREEZE_LOG.md for
# provenance; do not edit this copy independently of the source fixture.
_COMPANY_INFO_PATH = Path(__file__).resolve().parents[2] / "mock_data" / "company_info.json"


def _seller_context() -> str:
    """Build a short system-context blurb from the seller's company profile.

    Falls back to a minimal generic blurb if the fixture file is missing,
    so a bad path never prevents the agent from being constructed.
    """
    try:
        data = json.loads(_COMPANY_INFO_PATH.read_text(encoding="utf-8"))
        value_props = "\n".join(f"- {v}" for v in data["value_propositions"]["en"])
        terms = data["commercial_terms"]
        inside_sales = next(
            (p for p in data["sales_team"] if p["role_en"] == "Inside Sales"),
            data["sales_team"][0],
        )
        return (
            f"You are writing on behalf of {data['legal_name']} (brand: "
            f"{data['brand_name']}), based in {data['headquarters']['city']}, "
            f"{data['headquarters']['country']}. {data['business_domain']['en']}\n"
            f"Value propositions you may draw on:\n{value_props}\n"
            f"Commercial terms: delivery {terms['delivery']}; standard lead "
            f"time {terms['standard_lead_time_weeks']}; payment {terms['payment']}; "
            f"warranty {terms['warranty_months']} months.\n"
            f"Sign off as {inside_sales['name']} ({inside_sales['role_en']}) "
            "unless the research indicates an existing customer relationship, "
            "in which case a warmer, more familiar tone is appropriate."
        )
    except (OSError, KeyError, json.JSONDecodeError, IndexError):
        return "You are writing on behalf of PackFlow Systems GmbH, a German packaging machinery manufacturer."


class EmailDraftOutput(BaseModel):
    subject: str
    body: str


def get_email_draft_agent() -> Agent:
    drafter = Agent(
        model,
        instructions=(
            _seller_context() + "\n\n"
            "Your role is to draft a quotation reply email using the company "
            "research and catalog research you are given.\n"
            "- If company research is available, weave in a brief, natural "
            "reference to what the company does, so the reply reads as "
            "personalised rather than generic. If it says research was not "
            "available, do not guess or invent who the company is.\n"
            "- The catalog research is a list with one entry per product the "
            "sender asked about. Address every entry in your reply — for "
            "each one, if it was found, use only the product name, SKU, "
            "category and other details provided and confirm it briefly; if "
            "it was not found, say so politely for that specific item and "
            "ask for more detail. Never invent a product name or SKU that is "
            "not present in the research.\n"
            "- Each found entry may include a `description` and a `specs` "
            "object (throughput, gripper/sealing options, typical "
            "industries, etc.). If the sender asked a specific technical "
            "question (e.g. can it handle a particular container type, or "
            "should they use hot-melt vs tape), check `specs` first and "
            "answer using only what is written there. If `specs.options` "
            "lists something as requiring an engineering check (e.g. 'KLT / "
            "bin gripper (engineering check required)'), say the capability "
            "is available as an option but must be confirmed by engineering "
            "before it is quoted — never present it as an unconditional yes.\n"
            "- Do not invent prices, stock levels, or delivery dates beyond "
            "the standard lead time and terms given above."
        ),
        output_type=EmailDraftOutput,
    )
    return drafter

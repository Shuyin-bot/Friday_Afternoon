"""Mock business-data service for the PackFlow quotation demo.

Serves the frozen seller catalog and the inbound lead corpus, and exposes the
catalog matcher so the lead-to-product step can be demonstrated end to end.

Run from the repository root:

    uv run uvicorn mock_data.server:app --host 0.0.0.0 --port 8790 --reload

Interactive docs: http://localhost:8790/docs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Support both `uvicorn mock_data.server:app` (package) and `uvicorn server:app`
# (run from inside mock_data/), so a wrong working directory cannot break a demo.
try:
    from .matcher import MatchResult, match_lead, match_text
    from .product_catalog import get_catalog
except ImportError:  # pragma: no cover - fallback for non-package execution
    from matcher import MatchResult, match_lead, match_text
    from product_catalog import get_catalog

BASE_DIR = Path(__file__).parent
CATALOG_FILE = BASE_DIR / "product_catalog.json"
LEADS_FILE = BASE_DIR / "email_inbox.json"
OUTCOMES_FILE = BASE_DIR / "historical_lead_outcomes.json"

app = FastAPI(
    title="PackFlow Mock Data API",
    version="1.0",
    description=(
        "Frozen mock dataset for the quotation agent. "
        "`/match` endpoints resolve free-text lead enquiries against the product catalog."
    ),
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> Any:
    """Read a JSON dataset, or raise a 404 when it is absent."""
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset not available: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise HTTPException(status_code=500, detail=f"Malformed dataset {path.name}: {error}") from error


def _load_leads() -> list[dict]:
    """Return the raw lead records from the email corpus."""
    payload = _read_json(LEADS_FILE)
    leads = payload.get("leads") if isinstance(payload, dict) else payload
    if not isinstance(leads, list):
        raise HTTPException(status_code=500, detail="email_inbox.json has no 'leads' array")
    return leads


def _find_lead(lead_id: str) -> dict:
    """Return one lead by id, or raise a 404 without echoing dataset contents."""
    wanted = lead_id.strip().casefold()
    for lead in _load_leads():
        if str(lead.get("lead_id", "")).casefold() == wanted:
            return lead
    raise HTTPException(status_code=404, detail=f"Unknown lead_id: {lead_id}")


# --------------------------------------------------------------------------- #
# Meta
# --------------------------------------------------------------------------- #


@app.get("/", tags=["meta"], summary="Service health and dataset inventory")
def root() -> dict:
    """Report which datasets are present so a demo never starts blind."""
    return {
        "service": "PackFlow Mock Data API",
        "status": "ok",
        "datasets_available": {
            "product_catalog.json": CATALOG_FILE.is_file(),
            "email_inbox.json": LEADS_FILE.is_file(),
            "historical_lead_outcomes.json": OUTCOMES_FILE.is_file(),
        },
        "demo_path": ["/catalog", "/leads/LEAD-2026-016", "/match/LEAD-2026-016", "/match", "POST /match"],
        "docs": "/docs",
    }


# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #


@app.get("/catalog", tags=["catalog"], summary="Product catalog summary")
def catalog_summary() -> dict:
    """Return a compact view of the five catalog products."""
    catalog = get_catalog()
    return {
        "catalog_version": catalog.catalog_version,
        "currency": catalog.currency,
        "count": len(catalog.products),
        "products": [
            {
                "product_id": product.product_id,
                "model_code": product.model_code,
                "category": product.category.value,
                "name_en": product.name_en,
                "name_de": product.name_de,
                "max_throughput": product.specs.max_throughput,
                "price_range_eur": product.price_range_eur.model_dump(exclude_none=True),
                "lead_time_weeks": product.lead_time_weeks,
            }
            for product in catalog.products
        ],
    }


@app.get("/catalog/{product_id}", tags=["catalog"], summary="Full product specification")
def catalog_detail(product_id: str) -> dict:
    """Return every stored field for one product, including all spec anchors."""
    product = get_catalog().by_id(product_id.upper())
    if product is None:
        raise HTTPException(status_code=404, detail=f"Unknown product_id: {product_id}")
    return product.model_dump()


# --------------------------------------------------------------------------- #
# Leads
# --------------------------------------------------------------------------- #


@app.get("/leads", tags=["leads"], summary="Inbound lead index")
def list_leads() -> dict:
    """Return a compact index of every inbound lead."""
    leads = _load_leads()
    return {
        "count": len(leads),
        "leads": [
            {
                "lead_id": lead.get("lead_id"),
                "source_channel": lead.get("source_channel"),
                "timestamp": lead.get("timestamp"),
                "from": lead.get("raw_input", {}).get("from"),
                "subject": lead.get("raw_input", {}).get("subject"),
            }
            for lead in leads
        ],
    }


@app.get("/leads/{lead_id}", tags=["leads"], summary="One raw lead")
def get_lead(lead_id: str) -> dict:
    """Return one lead verbatim, including the untrusted email body."""
    return _find_lead(lead_id)


@app.get("/historical_lead_outcomes", tags=["leads"], summary="Scoring calibration corpus")
def historical_lead_outcomes() -> Any:
    """Return the historical scored cases used to calibrate fit scoring."""
    return _read_json(OUTCOMES_FILE)


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #


class MatchRequest(BaseModel):
    """Free-text enquiry to resolve against the catalog."""

    text: str = Field(min_length=1, description="Lead subject and/or body, German or English")
    subject: str | None = Field(default=None, description="Optional subject line")


@app.get("/match", tags=["match"], summary="Match every lead against the catalog")
def match_all() -> dict:
    """Resolve all leads and report coverage.

    An unmatched lead is a valid outcome: phishing, invoices, recruiter pitches
    and sponsorship requests mention no catalog product by design.
    """
    catalog = get_catalog()
    results = [match_lead(lead, catalog=catalog) for lead in _load_leads()]
    matched = [result for result in results if result.is_matched]
    return {
        "catalog_version": catalog.catalog_version,
        "leads_total": len(results),
        "leads_matched": len(matched),
        "leads_unmatched": len(results) - len(matched),
        "results": [
            {
                "lead_id": result.lead_id,
                "subject": result.subject,
                "matched_products": [match.model_code for match in result.matches],
                "matched_keywords": result.matched_keywords,
            }
            for result in results
        ],
    }


@app.get("/match/{lead_id}", tags=["match"], response_model=MatchResult, summary="Match one lead")
def match_one(lead_id: str) -> MatchResult:
    """Resolve one lead and return the products plus the keywords that matched."""
    return match_lead(_find_lead(lead_id))


@app.post("/match", tags=["match"], response_model=MatchResult, summary="Match arbitrary text")
def match_free_text(request: MatchRequest) -> MatchResult:
    """Resolve any enquiry text against the catalog.

    Use this to demonstrate live input. Terms outside the catalog -- for example
    a cartoning machine -- return no match instead of a nearest guess.
    """
    return match_text(request.text, subject=request.subject)

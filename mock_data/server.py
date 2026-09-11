"""Mock business-data service for the PackFlow quotation demo.

Serves the frozen seller catalog and the inbound lead corpus, and exposes the
catalog matcher so the lead-to-product step can be demonstrated end to end.

Run from the repository root:

    uv run uvicorn mock_data.server:app --host 0.0.0.0 --port 8790 --reload

Interactive docs: http://localhost:8790/docs
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Support both `uvicorn mock_data.server:app` (package) and `uvicorn server:app`
# (run from inside mock_data/), so a wrong working directory cannot break a demo.
try:
    from .catalog import get_catalog
    from .matcher import MatchResult, match_lead, match_text
except ImportError:  # pragma: no cover - fallback for non-package execution
    from catalog import get_catalog
    from matcher import MatchResult, match_lead, match_text

BASE_DIR = Path(__file__).parent
LEADS_FILE = BASE_DIR / "leads" / "email_inbox.json"

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


def _read_json(relative_path: str) -> Any:
    """Read a JSON file under `BASE_DIR`, or raise a 404 when it is absent."""
    path = BASE_DIR / relative_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset not available: {relative_path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise HTTPException(status_code=500, detail=f"Malformed dataset {relative_path}: {error}") from error


def _load_leads() -> list[dict]:
    """Return the raw lead records from the email corpus."""
    payload = _read_json("leads/email_inbox.json")
    leads = payload.get("leads") if isinstance(payload, dict) else payload
    if not isinstance(leads, list):
        raise HTTPException(status_code=500, detail="email_inbox.json has no 'leads' array")
    return leads


def _find_lead(lead_id: str) -> dict:
    """Return one lead by id, or raise a 404 listing nothing sensitive."""
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
    datasets = {
        "seller/product_catalog.json": (BASE_DIR / "seller/product_catalog.json").is_file(),
        "leads/email_inbox.json": LEADS_FILE.is_file(),
        "seller/company_info.json": (BASE_DIR / "seller/company_info.json").is_file(),
        "seller/historical_lead_outcomes.json": (BASE_DIR / "seller/historical_lead_outcomes.json").is_file(),
    }
    return {
        "service": "PackFlow Mock Data API",
        "status": "ok",
        "datasets_available": datasets,
        "key_endpoints": ["/catalog", "/leads", "/match", "/match/{lead_id}", "/docs"],
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


@app.get("/seller/product_catalog", tags=["catalog"], summary="Raw catalog file")
def raw_product_catalog() -> Any:
    """Return the catalog exactly as stored on disk."""
    return _read_json("seller/product_catalog.json")


@app.get("/seller/company_info", tags=["catalog"], summary="Seller company profile")
def company_info() -> Any:
    """Return the seller profile used for drafting and commercial terms."""
    return _read_json("seller/company_info.json")


@app.get("/seller/historical_lead_outcomes", tags=["catalog"], summary="Scoring calibration corpus")
def historical_lead_outcomes() -> Any:
    """Return the historical scored cases used to calibrate fit scoring."""
    return _read_json("seller/historical_lead_outcomes.json")


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


@app.get("/leads/email_inbox", include_in_schema=False)
def raw_email_inbox() -> Any:
    """Return the raw lead corpus file (kept for backwards compatibility)."""
    return _read_json("leads/email_inbox.json")


@app.get("/leads/badge_scan_export", tags=["leads"], summary="Trade-fair badge scans")
def badge_scan_export() -> list[dict]:
    """Return badge scans parsed with the standard library, if the file exists."""
    path = BASE_DIR / "leads" / "badge_scan_export.csv"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Dataset not available: leads/badge_scan_export.csv")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


# Declared after the static /leads/* paths: FastAPI resolves routes in
# definition order, so a path parameter here would otherwise swallow them.
@app.get("/leads/{lead_id}", tags=["leads"], summary="One raw lead")
def get_lead(lead_id: str) -> dict:
    """Return one lead verbatim, including the untrusted email body."""
    return _find_lead(lead_id)


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

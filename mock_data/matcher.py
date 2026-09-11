"""Match inbound lead text against the frozen product catalog.

Leads arrive as free-text German/English email bodies; the catalog is keyed by
model code. This module bridges the two with an explicit synonym table so that
every match is traceable to a keyword an operator can read and audit.

No fuzzy scoring and no LLM: a lead that mentions nothing in the catalog must
come back empty rather than be assigned the "closest" product.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .product_catalog import Product, ProductCatalog, ProductCategory, get_catalog

# Keyword -> category. German first (the seller's main market), then English.
# Substring matching is intentional: "Kartonaufrichters" contains
# "kartonaufrichter", and "Palettierzelle"/"Palettierer" both contain "palettier".
CATEGORY_KEYWORDS: dict[ProductCategory, tuple[str, ...]] = {
    ProductCategory.CASE_ERECTOR: (
        "kartonaufrichter",
        "aufrichter",
        "case erector",
        "caseerector",
        "erector",
        "pfs-ce",
    ),
    ProductCategory.CARTON_SEALER: (
        "kartonverschließer",
        "kartonverschliesser",
        "verschließer",
        "verschliesser",
        "carton sealer",
        "case sealer",
        "sealer",
        "pfs-cs",
    ),
    ProductCategory.WRAP_AROUND_PACKER: (
        "wrap-around",
        "wrap around",
        "wraparound",
        "wickelpacker",
        # The catalog name is "Wrap-Around Case Packer", so the generic trade
        # term for the category has to resolve here too.
        "case packer",
        "casepacker",
        "kartonpacker",
        "pfs-wa",
    ),
    ProductCategory.PALLETIZING_CELL: (
        "palettier",
        "palletiz",
        "palletis",
        "palettierzelle",
        "robotik",
        "pfs-pal",
    ),
    ProductCategory.FORMAT_AND_WEAR_PARTS: (
        "formatsatz",
        "formatsätze",
        "formatsaetze",
        "format set",
        "verschleißteil",
        "verschleissteil",
        "wear part",
        "ersatzteil",
        "spare part",
        "pfs-fs",
    ),
}


class ProductMatch(BaseModel):
    """One catalog product matched to a lead, with the evidence that matched it."""

    model_config = ConfigDict(frozen=True)

    product_id: str
    model_code: str
    category: ProductCategory
    name_en: str
    matched_keywords: list[str] = Field(default_factory=list)
    price_range_eur: dict = Field(default_factory=dict)
    lead_time_weeks: str
    max_throughput: str | None = None


class MatchResult(BaseModel):
    """Matching outcome for one lead.

    `matches` is empty when the lead mentions nothing in the catalog. That is a
    valid, expected result -- phishing, invoices and no-context enquiries must
    not be mapped onto a product.
    """

    model_config = ConfigDict(frozen=True)

    lead_id: str | None = None
    subject: str | None = None
    matches: list[ProductMatch] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    catalog_version: str

    @property
    def is_matched(self) -> bool:
        """Return whether at least one catalog product was identified."""
        return bool(self.matches)


def _to_match(product: Product, keywords: list[str]) -> ProductMatch:
    """Build a `ProductMatch` from a catalog product and its matched keywords."""
    return ProductMatch(
        product_id=product.product_id,
        model_code=product.model_code,
        category=product.category,
        name_en=product.name_en,
        matched_keywords=sorted(keywords),
        price_range_eur=product.price_range_eur.model_dump(exclude_none=True),
        lead_time_weeks=product.lead_time_weeks,
        max_throughput=product.specs.max_throughput,
    )


def match_text(
    text: str,
    catalog: ProductCatalog | None = None,
    lead_id: str | None = None,
    subject: str | None = None,
) -> MatchResult:
    """Match free-text lead content against the catalog by keyword."""
    catalog = catalog or get_catalog()
    haystack = text.casefold()

    hits: dict[ProductCategory, list[str]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword in haystack]
        if found:
            hits[category] = found

    matches: list[ProductMatch] = []
    for product in catalog.products:
        keywords = hits.get(product.category)
        if keywords:
            matches.append(_to_match(product, keywords))

    return MatchResult(
        lead_id=lead_id,
        subject=subject,
        matches=matches,
        matched_keywords=sorted({keyword for found in hits.values() for keyword in found}),
        catalog_version=catalog.catalog_version,
    )


def match_lead(lead: dict, catalog: ProductCatalog | None = None) -> MatchResult:
    """Match one raw lead record from `leads/email_inbox.json`."""
    raw = lead.get("raw_input", {})
    subject = raw.get("subject") or ""
    body = raw.get("body") or ""
    return match_text(
        f"{subject}\n{body}",
        catalog=catalog,
        lead_id=lead.get("lead_id"),
        subject=subject,
    )

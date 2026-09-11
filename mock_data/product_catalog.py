"""Typed access to the frozen PackFlow product catalog.

The catalog is the grounding anchor for the drafting and scoring agents: every
factual claim about throughput, format range, price or lead time must be
traceable to a `Product` loaded here. Nothing in this module invents values.
"""

from __future__ import annotations

import json
from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CATALOG_PATH = Path(__file__).parent / "seller" / "product_catalog.json"


class ProductCategory(str, Enum):
    """Machine families offered in the catalog."""

    CASE_ERECTOR = "case_erector"
    CARTON_SEALER = "carton_sealer"
    WRAP_AROUND_PACKER = "wrap_around_packer"
    PALLETIZING_CELL = "palletizing_cell"
    FORMAT_AND_WEAR_PARTS = "format_and_wear_parts"


class CartonRange(BaseModel):
    """Carton dimension range in millimetres, stored as inclusive `min-max` strings."""

    model_config = ConfigDict(frozen=True)

    length: str
    width: str
    height: str


class ProductSpecs(BaseModel):
    """Technical specification block.

    Fields differ per machine family, so unknown keys are preserved instead of
    discarded: dropping a spec silently would let an agent claim a capability
    the catalog never stated.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    max_throughput: str | None = None
    carton_standard: str | None = None
    carton_range_mm: CartonRange | None = None
    sealing: str | None = None
    bottom_sealing: str | None = None
    power: str | None = None
    compressed_air: str | None = None
    footprint_mm: str | None = None
    weight_kg: int | None = Field(default=None, gt=0)
    control: str | None = None
    connectivity: str | None = None
    options: list[str] = Field(default_factory=list)
    typical_industries: list[str] = Field(default_factory=list)


class PriceRange(BaseModel):
    """List-price band in EUR, EXW Heilbronn, excluding VAT.

    Machines use `min`/`max`; the spare-parts entry uses per-kit bands instead,
    so every field is optional and extra keys are kept.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    min: int | None = Field(default=None, gt=0)
    max: int | None = Field(default=None, gt=0)


class Product(BaseModel):
    """One catalog entry with bilingual copy and a traceable price band."""

    model_config = ConfigDict(frozen=True)

    product_id: str = Field(min_length=1)
    model_code: str = Field(min_length=1)
    category: ProductCategory
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    specs: ProductSpecs
    moq: str
    price_range_eur: PriceRange
    lead_time_weeks: str

    def matches(self, term: str) -> bool:
        """Return whether `term` appears in this product's identifiers or copy."""
        needle = term.casefold().strip()
        if not needle:
            return False
        haystack = " ".join(
            (
                self.product_id,
                self.model_code,
                self.category.value,
                self.name_de,
                self.name_en,
                self.description_de,
                self.description_en,
            )
        ).casefold()
        return needle in haystack


class ProductCatalog(BaseModel):
    """Frozen catalog snapshot identified by `catalog_version`."""

    model_config = ConfigDict(frozen=True)

    catalog_version: str = Field(min_length=1)
    currency: str = Field(min_length=1)
    note: str = ""
    products: list[Product]

    def by_id(self, product_id: str) -> Product | None:
        """Return the product with `product_id`, or `None` when absent."""
        return next((item for item in self.products if item.product_id == product_id), None)

    def by_category(self, category: ProductCategory) -> list[Product]:
        """Return every product in `category`, preserving catalog order."""
        return [item for item in self.products if item.category is category]

    def search(self, terms: list[str]) -> tuple[list[Product], list[str]]:
        """Resolve `terms` against the catalog.

        Returns the matched products and the terms that matched nothing, so the
        caller can report unresolved requests instead of guessing a substitute.
        """
        found: dict[str, Product] = {}
        unresolved: list[str] = []
        for term in terms:
            matches = [item for item in self.products if item.matches(term)]
            if not matches:
                unresolved.append(term)
                continue
            found.update({item.product_id: item for item in matches})
        return list(found.values()), unresolved


def load_catalog(path: str | Path = CATALOG_PATH) -> ProductCatalog:
    """Read and validate the catalog at `path`."""
    return ProductCatalog.model_validate_json(Path(path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_catalog() -> ProductCatalog:
    """Return the default catalog, parsed once per process."""
    return load_catalog()


if __name__ == "__main__":
    catalog = get_catalog()
    print(f"catalog {catalog.catalog_version} ({catalog.currency}), {len(catalog.products)} products")
    for product in catalog.products:
        band = product.price_range_eur.model_dump(exclude_none=True)
        print(f"  {product.product_id:<12} {product.category.value:<24} {json.dumps(band)}")

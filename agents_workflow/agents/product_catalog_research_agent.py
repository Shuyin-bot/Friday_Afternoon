import json

from pydantic import BaseModel
from pydantic_ai import Agent

from db_contexts.models import Product
from db_contexts.repos.product_repository import (
    get_product_by_alias,
    get_product_by_sku,
    search_products,
)
from vector_contexts import get_product_collection

from ..provider.base_provider import model


class InternalResearchOutput(BaseModel):
    product: str | None = None
    found: bool
    source: str | None = None
    sku: str | None = None
    name: str | None = None
    category: str | None = None


def _product_payload(product: Product) -> dict:
    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category.value,
        "description": product.description,
        "box_style": product.box_style,
        "material": product.material,
        "dimensions": product.dimensions,
    }


def find_product_in_catalog(product: str) -> str:
    """Find a product with SQL search, then semantic search if nothing is found."""
    matches = []
    source = "sql"

    found = get_product_by_sku(product) or get_product_by_alias(product)
    if found:
        matches = [found]
    else:
        matches = search_products(product)

    if not matches:
        source = "semantic"
        result = get_product_collection().query(query_texts=[product], n_results=3)
        ids = (result.get("ids") or [[]])[0]
        for sku in ids:
            item = get_product_by_sku(sku)
            if item:
                matches.append(item)

    return json.dumps({
        "source": source,
        "found": bool(matches),
        "matches": [_product_payload(item) for item in matches],
    })


def get_internal_research_agent() -> Agent:
    researcher = Agent(
        model,
        instructions=(
            "Your role is to check whether a requested product exists in the "
            "internal catalog. Use the find_product_in_catalog tool with the "
            "product name. Prefer exact catalog matches. If nothing is found, "
            "return found as False instead of guessing."
        ),
        output_type=InternalResearchOutput,
        tools=[find_product_in_catalog],
    )
    return researcher

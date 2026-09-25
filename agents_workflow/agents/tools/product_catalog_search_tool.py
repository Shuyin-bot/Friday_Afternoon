from db_contexts.models import Product
from db_contexts.repos.product_repository import (
    get_product_by_alias,
    get_product_by_sku,
    search_products,
)
from vector_contexts import search_products_semantic

from ..core_models import ProductSearchOutput, ProductSummary
from .tool_logger import log_tool_use


def product_catalog_search_tool(
    sku: str = "",
    alias: str = "",
    name: str = "",
    description: str = "",
) -> ProductSearchOutput:
    """Find a requested product in the internal catalog."""
    log_tool_use(
        "product_catalog_search_tool",
        f"sku={bool(sku)}, alias={bool(alias)}, name={bool(name)}, description={bool(description)}",
    )
    matches = []
    seen = set()

    def add(product: Product | None) -> None:
        if product and product.sku not in seen:
            seen.add(product.sku)
            matches.append(product)

    if sku:
        add(get_product_by_sku(sku))
    if alias:
        add(get_product_by_alias(alias))
    for term in (name, description):
        if term:
            for item in search_products(term):
                add(item)

    query = " ".join(part for part in (sku, alias, name, description) if part)
    source = "sql"
    if not matches and query:
        source = "semantic"
        for found_sku in search_products_semantic(query):
            add(get_product_by_sku(found_sku))

    return ProductSearchOutput(
        search_term=query,
        found=bool(matches),
        source=source,
        products=[
            ProductSummary(
                sku=item.sku,
                name=item.name,
                category=item.category.value,
                description=item.description,
                box_style=item.box_style,
                material=item.material,
                dimensions=item.dimensions,
            )
            for item in matches
        ],
    )

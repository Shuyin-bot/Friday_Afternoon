from typing import Any

from db_contexts.repos.product_repository import get_product_by_sku, get_product_prices

from ..core_models import QuotationLine, QuotationPriceOutput
from .tool_logger import log_tool_use


def calculate_quotation_price_tool(
    product_list: list[QuotationLine],
) -> QuotationPriceOutput:
    """Price a quotation from matched products and requested quantities."""
    log_tool_use("calculate_quotation_price_tool", f"lines={len(product_list)}")
    total = 0.0
    lines = []
    missing_products = []

    for line in product_list:
        product = get_product_by_sku(line.sku) if line.sku else None
        if not product:
            missing_products.append(line.product_name)
            lines.append(line)
            continue

        quantity = line.quantity
        unit_price = None
        for price in get_product_prices(product.id):
            if price.minimum_quantity <= quantity:
                unit_price = price.unit_price
        if unit_price is None:
            unit_price = product.price_min_eur
        if unit_price is None:
            missing_products.append(product.name)
            lines.append(QuotationLine(
                product_name=product.name,
                sku=product.sku,
                quantity=quantity,
            ))
            continue

        line_total = float(unit_price) * quantity
        lines.append(QuotationLine(
            product_name=product.name,
            sku=product.sku,
            quantity=quantity,
            unit_price=float(unit_price),
            line_total=line_total,
        ))
        total += line_total

    return QuotationPriceOutput(
        lines=lines,
        total=total if lines and not missing_products else None,
        missing_products=missing_products,
    )

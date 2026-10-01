import json
from pathlib import Path
from typing import Any

from ..core_models import QuotationDraftOutput
from .tool_logger import log_tool_use


_COMPANY_INFO_PATH = Path(__file__).resolve().parents[3] / "mock_data" / "company_info.json"


def _seller_signature() -> str:
    try:
        data = json.loads(_COMPANY_INFO_PATH.read_text(encoding="utf-8"))
        inside_sales = next(
            person for person in data["sales_team"] if person["role_en"] == "Inside Sales"
        )
        return (
            f"{inside_sales['name']}\n"
            f"{inside_sales['role_en']}\n"
            f"{data['legal_name']}\n"
            f"{inside_sales['email']}"
        )
    except (OSError, KeyError, json.JSONDecodeError, StopIteration):
        return "Jonas Brenner\nInside Sales\nPackFlow Systems GmbH\nj.brenner@packflow-systems.de"


def draft_quotation_email_tool(
    company_name: str = "",
    contact_person: str = "",
    product_lines: list[dict[str, Any]] | None = None,
    total: float | None = None,
    missing_products: list[str] | None = None,
    other_requirements: str = "",
) -> QuotationDraftOutput:
    """Draft a quotation reply from extracted and calculated data."""
    log_tool_use("draft_quotation_email_tool", f"lines={len(product_lines or [])}")
    greeting = f"Dear {contact_person}," if contact_person else "Hello,"
    lines = [greeting, "", "Thank you for your quotation request.", ""]

    if company_name:
        lines.extend([
            f"We have prepared the following information for {company_name}:",
            "",
        ])

    for item in product_lines or []:
        name = item.get("name", "Requested product")
        sku = item.get("sku")
        quantity = item.get("quantity")
        unit_price = item.get("unit_price")
        line_total = item.get("line_total")
        label = f"{name} ({sku})" if sku else name
        if quantity is not None:
            label = f"{label} - quantity: {quantity}"
        if unit_price is None or line_total is None:
            lines.append(f"- {label}: price to be confirmed")
        else:
            lines.append(
                f"- {label}: EUR {unit_price:.2f} each, "
                f"line total EUR {line_total:.2f}"
            )

    if total is not None:
        lines.extend(["", f"Total: EUR {total:.2f}"])
    if missing_products:
        lines.extend([
            "",
            "We could not confirm the following requested products in our catalog:",
            *[f"- {product}" for product in missing_products],
        ])
    if other_requirements:
        lines.extend(["", f"Your other requirements: {other_requirements}"])

    lines.extend([
        "",
        "Please let us know if you would like to provide any missing details.",
        "Kind regards,",
        _seller_signature(),
    ])
    return QuotationDraftOutput(
        subject="Quotation Request",
        body="\n".join(lines),
    )

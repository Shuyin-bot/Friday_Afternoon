from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    sku: str
    name: str
    category: str
    description: str
    box_style: str | None = None
    material: str | None = None
    dimensions: str | None = None


class ProductSearchOutput(BaseModel):
    search_term: str
    found: bool
    source: str | None = None
    products: list[ProductSummary] = Field(default_factory=list)


class CompanyResearchOutput(BaseModel):
    company: str
    summary: str | None = None
    website: str | None = None
    industry: str | None = None
    company_size: str | None = None
    sources: list[str] = Field(default_factory=list)


class QuotationLine(BaseModel):
    product_name: str
    sku: str | None = None
    quantity: int = Field(gt=0)
    unit_price: float | None = None
    line_total: float | None = None
    currency: str = "EUR"


class QuotationPriceOutput(BaseModel):
    lines: list[QuotationLine] = Field(default_factory=list)
    total: float | None = None
    currency: str = "EUR"
    missing_products: list[str] = Field(default_factory=list)


class QuotationDraftOutput(BaseModel):
    subject: str
    body: str

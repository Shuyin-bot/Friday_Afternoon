from datetime import datetime

from db_contexts.models import (
    Inventory,
    PriceList,
    Product,
    ProductAlias,
    ProductCategory,
    ProductPrice,
    Warehouse,
)
from db_contexts.sessions import SessionLocal
from sqlalchemy import func, or_


def create_product(
    sku: str,
    name: str,
    category: ProductCategory,
    description: str,
    box_style: str | None = None,
    material: str | None = None,
    dimensions: str | None = None,
    unit_of_measure: str | None = None,
    aliases: list[str] | None = None,
    name_de: str | None = None,
    description_de: str | None = None,
    specs_json: str | None = None,
    moq: str | None = None,
    price_min_eur: float | None = None,
    price_max_eur: float | None = None,
    lead_time_weeks: str | None = None,
) -> Product:
    with SessionLocal() as session:
        product = Product(
            sku=sku,
            name=name,
            category=category,
            description=description,
            box_style=box_style,
            material=material,
            dimensions=dimensions,
            unit_of_measure=unit_of_measure,
            name_de=name_de,
            description_de=description_de,
            specs_json=specs_json,
            moq=moq,
            price_min_eur=price_min_eur,
            price_max_eur=price_max_eur,
            lead_time_weeks=lead_time_weeks,
        )
        session.add(product)
        session.flush()

        for alias in aliases or []:
            session.add(ProductAlias(product_id=product.id, alias=alias))

        session.commit()
        return product


def get_product_by_id(product_id: int) -> Product | None:
    with SessionLocal() as session:
        return session.query(Product).filter_by(id=product_id).first()


def get_product_by_sku(sku: str) -> Product | None:
    with SessionLocal() as session:
        return session.query(Product).filter(
            func.lower(Product.sku) == sku.strip().lower()
        ).first()


def search_products(search_term: str) -> list[Product]:
    term = f"%{search_term.strip()}%"
    with SessionLocal() as session:
        return session.query(Product).filter(
            or_(
                Product.sku.ilike(term),
                Product.name.ilike(term),
                Product.description.ilike(term),
            ),
            Product.is_active.is_(True),
        ).all()


def get_product_by_alias(alias: str) -> Product | None:
    with SessionLocal() as session:
        return session.query(Product).join(ProductAlias).filter(
            func.lower(ProductAlias.alias) == alias.strip().lower(),
            Product.is_active.is_(True),
        ).first()


def get_products_by_category(category: ProductCategory) -> list[Product]:
    with SessionLocal() as session:
        return session.query(Product).filter(
            Product.category == category,
            Product.is_active.is_(True),
        ).all()


def get_product_inventory(product_id: int) -> list[Inventory]:
    with SessionLocal() as session:
        return session.query(Inventory).join(Warehouse).filter(
            Inventory.product_id == product_id,
        ).all()


def get_product_prices(
    product_id: int,
    currency: str = "EUR",
    at_time: datetime | None = None,
) -> list[ProductPrice]:
    at_time = at_time or datetime.now()
    with SessionLocal() as session:
        return session.query(ProductPrice).join(PriceList).filter(
            ProductPrice.product_id == product_id,
            PriceList.currency == currency,
            PriceList.is_active.is_(True),
            ProductPrice.valid_from <= at_time,
            or_(
                ProductPrice.valid_until.is_(None),
                ProductPrice.valid_until > at_time,
            ),
        ).order_by(ProductPrice.minimum_quantity).all()

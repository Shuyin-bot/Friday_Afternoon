from datetime import datetime, timezone

from sqlalchemy import func, or_, select

from db_contexts.models import Inventory, PriceList, Product, ProductAlias, ProductPrice, Warehouse
from db_contexts.sessions import SessionLocal


def create_product(
    sku: str,
    name: str,
    category,
    description: str,
    box_style: str,
    material: str,
    dimensions: str,
    aliases: list[str] | None = None,
) -> Product:
    """Create one catalogue product and its customer-facing aliases."""
    with SessionLocal.begin() as session:
        product = Product(
            sku=sku,
            name=name,
            category=category,
            description=description,
            box_style=box_style,
            material=material,
            dimensions=dimensions,
        )
        product.aliases = [ProductAlias(alias=alias) for alias in aliases or []]
        session.add(product)
        session.flush()
        session.refresh(product)
        return product


def find_exact_product(search_text: str) -> Product | None:
    """Find an active product by exact SKU, name, or alias."""
    value = search_text.strip().casefold()
    with SessionLocal() as session:
        return session.scalar(
            select(Product)
            .outerjoin(ProductAlias)
            .where(
                Product.is_active.is_(True),
                or_(
                    func.lower(func.trim(Product.sku)) == value,
                    func.lower(func.trim(Product.name)) == value,
                    func.lower(func.trim(ProductAlias.alias)) == value,
                ),
            )
            .limit(1)
        )


def list_products() -> list[Product]:
    """Return active products for catalogue display or vector indexing."""
    with SessionLocal() as session:
        return list(session.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name)).all())


def get_inventory(product_id: int, warehouse_code: str | None = None) -> list[Inventory]:
    """Return inventory records for a product, optionally limited to a warehouse."""
    with SessionLocal() as session:
        statement = select(Inventory).join(Warehouse).where(Inventory.product_id == product_id)
        if warehouse_code:
            statement = statement.where(Warehouse.code == warehouse_code)
        return list(session.scalars(statement).all())


def get_current_price(
    product_id: int,
    currency: str = "USD",
    quantity: int = 1,
    as_of: datetime | None = None,
) -> ProductPrice | None:
    """Return the highest applicable quantity price from an active price list."""
    timestamp = as_of or datetime.now(timezone.utc)
    with SessionLocal() as session:
        return session.scalar(
            select(ProductPrice)
            .join(PriceList)
            .where(
                ProductPrice.product_id == product_id,
                PriceList.currency == currency,
                PriceList.is_active.is_(True),
                ProductPrice.minimum_quantity <= quantity,
                ProductPrice.valid_from <= timestamp,
                or_(ProductPrice.valid_until.is_(None), ProductPrice.valid_until >= timestamp),
            )
            .order_by(ProductPrice.minimum_quantity.desc())
            .limit(1)
        )

import json
from datetime import datetime, timezone
from pathlib import Path

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
from vector_contexts import get_product_collection


DATA_FILE = Path(__file__).parents[1] / "mock_data" / "product_seed.json"
NOW = datetime.now(timezone.utc)


def load_product_data():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    with SessionLocal() as session:
        price_lists = {}
        for item in data["price_lists"]:
            price_list = session.query(PriceList).filter_by(name=item["name"]).first()
            if not price_list:
                price_list = PriceList(**item)
                session.add(price_list)
                session.flush()
            price_lists[item["currency"]] = price_list

        warehouses = {}
        for item in data["warehouses"]:
            warehouse = session.query(Warehouse).filter_by(code=item["code"]).first()
            if not warehouse:
                warehouse = Warehouse(
                    code=item["code"],
                    name=item["name"],
                    location=item["location"],
                )
                session.add(warehouse)
                session.flush()
            warehouses[item["code"]] = (warehouse, item["inventory"])

        collection = get_product_collection()
        documents = []
        metadatas = []
        ids = []

        for item in data["products"]:
            product = session.query(Product).filter_by(sku=item["sku"]).first()
            if not product:
                product = Product(
                    sku=item["sku"],
                    name=item["name"],
                    category=ProductCategory(item["category"]),
                    description=item["description"],
                    box_style=item["box_style"],
                    material=item["material"],
                    dimensions=item["dimensions"],
                    unit_of_measure=item["unit_of_measure"],
                )
                session.add(product)
                session.flush()

                for alias in item["aliases"]:
                    session.add(ProductAlias(product_id=product.id, alias=alias))

                for price in item["prices"]:
                    session.add(ProductPrice(
                        product_id=product.id,
                        price_list_id=price_lists["EUR"].id,
                        minimum_quantity=price["minimum_quantity"],
                        unit_price=price["unit_price"],
                        valid_from=NOW,
                    ))

                for warehouse, inventory in warehouses.values():
                    session.add(Inventory(
                        product_id=product.id,
                        warehouse_id=warehouse.id,
                        quantity_on_hand=inventory.get(product.sku, 0),
                    ))

            ids.append(product.sku)
            documents.append(
                f"{product.name}. {product.description} "
                f"Category: {product.category.value}. "
                f"Style: {product.box_style}. Material: {product.material}. "
                f"Dimensions: {product.dimensions}."
            )
            metadatas.append({"sku": product.sku, "category": product.category.value})

        session.commit()
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"loaded {len(ids)} products into SQLite and Chroma")


if __name__ == "__main__":
    load_product_data()

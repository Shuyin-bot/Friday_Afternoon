"""Load the PackFlow machine catalog into SQLite and the Chroma products
collection.

The machine catalog (`mock_data/product_catalog.json`) describes packaging
*machines* (case erectors, carton sealers, wrap-around packers, palletizing
cells, and format/wear-part kits), as opposed to `product_seed.json` which
describes packaging *materials* (boxes, mailers, cartons). Both sets are
loaded into the same `products` table and the same Chroma collection so that
`find_product_in_catalog` (SQL exact match, then Chroma semantic search) can
find either kind of product without any code changes.

Machine-specific attributes (specs, MOQ, price range, lead time, German
name/description) are stored in nullable columns added to the `Product`
model; they are simply left NULL for packaging-material rows and vice versa.
"""
import json
from pathlib import Path

from db_contexts.models import Product, ProductAlias, ProductCategory
from db_contexts.sessions import SessionLocal
from vector_contexts import get_product_collection


DATA_FILE = Path(__file__).parents[1] / "mock_data" / "product_catalog.json"


def _price_bounds(price_range: dict) -> tuple[float | None, float | None]:
    """Best-effort extraction of a numeric min/max from a price_range_eur dict.

    Some catalog entries (e.g. format_and_wear_parts) use nested keys such as
    `format_set_min` / `wear_kit_max` instead of a plain `min` / `max`. In
    that case we take the overall min and max across every numeric value
    present, rather than inventing a single "the" price.
    """
    if "min" in price_range and "max" in price_range:
        return price_range["min"], price_range["max"]

    numeric_values = [v for v in price_range.values() if isinstance(v, (int, float))]
    if not numeric_values:
        return None, None
    return min(numeric_values), max(numeric_values)


def load_machine_catalog():
    # 1. 读取Json文件
    # 1. Load the machine catalog JSON into SQLite and the Chroma products collection.
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    with SessionLocal() as session:
        collection = get_product_collection()
        documents = []
        metadatas = []
        ids = []

        for item in data["products"]:
            sku = item["product_id"]
            product = session.query(Product).filter_by(sku=sku).first()

            price_min, price_max = _price_bounds(item.get("price_range_eur", {}))

            if not product:
                # 2. 创建或更新数据库记录
                # 2. If the product doesn't exist yet, create it and any alias.
                product = Product(
                    sku=sku,
                    name=item["name_en"],
                    category=ProductCategory(item["category"].upper()),
                    description=item["description_en"],
                    name_de=item.get("name_de"),
                    description_de=item.get("description_de"),
                    specs_json=json.dumps(item.get("specs", {})),
                    moq=item.get("moq"),
                    price_min_eur=price_min,
                    price_max_eur=price_max,
                    lead_time_weeks=item.get("lead_time_weeks"),
                )
                session.add(product)
                session.flush()

                # model_code is a common shorthand customers use in emails
                # (e.g. "PFS-CE 240" instead of the product_id "PFS-CE-240").
                model_code = item.get("model_code")
                if model_code and model_code != sku:
                    session.add(ProductAlias(product_id=product.id, alias=model_code))
            else:
                product.name = item["name_en"]
                product.category = ProductCategory(item["category"].upper())
                product.description = item["description_en"]
                product.name_de = item.get("name_de")
                product.description_de = item.get("description_de")
                product.specs_json = json.dumps(item.get("specs", {}))
                product.moq = item.get("moq")
                product.price_min_eur = price_min
                product.price_max_eur = price_max
                product.lead_time_weeks = item.get("lead_time_weeks")

            ids.append(sku)
            documents.append(
                f"{item['name_en']}. {item['description_en']} "
                f"Category: {item['category']}. "
                f"Typical industries: {', '.join(item.get('specs', {}).get('typical_industries', []))}."
            )
            metadatas.append({"sku": sku, "category": item["category"]})

        session.commit()
        # 3. 将数据加载到Chroma向量数据库
        # 3. Load the data into the Chroma vector database.
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"loaded {len(ids)} machines into SQLite and Chroma")


if __name__ == "__main__":
    load_machine_catalog()

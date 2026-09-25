import os
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "data/chroma"))
PRODUCT_COLLECTION = os.getenv("CHROMA_PRODUCT_COLLECTION", "products")


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """Return the local persistent Chroma client."""
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


@lru_cache(maxsize=1)
def get_product_collection() -> Collection:
    """Return the collection used for product embeddings."""
    return get_chroma_client().get_or_create_collection(name=PRODUCT_COLLECTION)


def search_products_semantic(query: str, n_results: int = 3) -> list[str]:
    """Return catalog SKUs that semantically match `query`."""
    result = get_product_collection().query(query_texts=[query], n_results=n_results)
    return (result.get("ids") or [[]])[0]

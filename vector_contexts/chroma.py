import os
from pathlib import Path
from threading import RLock

import chromadb
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "data/chroma"))
PRODUCT_COLLECTION = os.getenv("CHROMA_PRODUCT_COLLECTION", "products")
COMPANY_RESEARCH_COLLECTION = os.getenv(
    "CHROMA_COMPANY_RESEARCH_COLLECTION", "company_research"
)
_chroma_lock = RLock()
_client = None
_product_collection = None
_company_research_collection = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return the local persistent Chroma client."""
    global _client
    with _chroma_lock:
        if _client is None:
            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        return _client


def get_product_collection() -> Collection:
    """Return the collection used for product embeddings."""
    global _product_collection
    client = get_chroma_client()
    with _chroma_lock:
        if _product_collection is None:
            _product_collection = client.get_or_create_collection(
                name=PRODUCT_COLLECTION
            )
        return _product_collection


def get_company_research_collection() -> Collection:
    """Return the collection used for company research embeddings."""
    global _company_research_collection
    client = get_chroma_client()
    with _chroma_lock:
        if _company_research_collection is None:
            _company_research_collection = client.get_or_create_collection(
                name=COMPANY_RESEARCH_COLLECTION
            )
        return _company_research_collection


def search_products_semantic(query: str, n_results: int = 3) -> list[str]:
    """Return catalog SKUs that semantically match `query`."""
    result = get_product_collection().query(query_texts=[query], n_results=n_results)
    return (result.get("ids") or [[]])[0]


def search_company_research_semantic(query: str, n_results: int = 3) -> list[str]:
    """Return company research IDs that semantically match `query`."""
    result = get_company_research_collection().query(
        query_texts=[query], n_results=n_results
    )
    return (result.get("ids") or [[]])[0]

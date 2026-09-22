import json

from pydantic import BaseModel
from pydantic_ai import Agent

from db_contexts.models import Product
from db_contexts.repos.product_repository import (
    get_product_by_alias,
    get_product_by_sku,
    search_products,
)
from vector_contexts import get_product_collection

from ..provider.base_provider import model


class InternalResearchOutput(BaseModel):
    product: str | None = None
    found: bool
    source: str | None = None
    sku: str | None = None
    name: str | None = None
    category: str | None = None


def _product_payload(product: Product) -> dict:
    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category.value,
        "description": product.description,
        "box_style": product.box_style,
        "material": product.material,
        "dimensions": product.dimensions,
    }


def find_product_in_catalog(product: str) -> str:
    """Find a product with SQL search, then semantic search if nothing is found."""
    matches = [] # 搜索结果列表
    source = "sql" # 记录用了哪种搜索策略

    # ========== 策略1：精确匹配 (最快) ========== 
    # 尝试SKU精确匹配或别名匹配
    found = get_product_by_sku(product) or get_product_by_alias(product)
    if found:
        matches = [found] # 找到了，直接返回
    else:
        # ========== 策略2：模糊匹配 (中等速度) ==========
        # SQL LIKE查询
        matches = search_products(product)
        # 等价于：
        # SELECT * FROM products 
        # WHERE sku LIKE '%装箱机%' 
        #    OR name LIKE '%装箱机%' 
        #    OR description LIKE '%装箱机%'

     # ========== 策略3：语义搜索 (最智能) ✨ ==========
    if not matches:
        source = "semantic" # 标记：使用向量搜索

        # 使用ChromaDB进行语义搜索
        result = get_product_collection().query(
            query_texts=[product], # 用户输入的查询文本
            n_results=3)       # 返回前3个最相似的结果
        # ChromaDB内部流程：
        # 1. 将 "装箱机" 转换为向量 [0.23, -0.45, 0.67, ...]
        # 2. 计算与所有产品向量的余弦相似度
        # 3. 返回相似度最高的3个产品的ID (SKU)

        # 解析结果
        ids = (result.get("ids") or [[]])[0]
        # result结构：
        # {
        #   "ids": [["PFS-CE-240", "PFS-CE-180", "PFS-CS-180"]],
        #   "distances": [[0.12, 0.23, 0.34]],  # 越小越相似
        #   "metadatas": [[{...}, {...}, {...}]]
        # }

        # 根据SKU从SQLite获取完整产品信息
        for sku in ids:
            item = get_product_by_sku(sku)
            if item:
                matches.append(item)

    # 返回JSON格式的结果
    return json.dumps({
        "source": source,
        "found": bool(matches),
        "matches": [_product_payload(item) for item in matches],
    })

# modify
def get_internal_research_agent() -> Agent:
    researcher = Agent(
        model,
        instructions=(
            "Your role is to check whether a requested product exists in the "
            "internal catalog. Use the find_product_in_catalog tool with the "
            "product name. Prefer catalog matches. If nothing is found, "
            "return found as False instead of guessing."
        ),
        output_type=InternalResearchOutput,
        tools=[find_product_in_catalog],
    )
    return researcher

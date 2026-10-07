import re

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from ..models import Product, Provider, doc_to_model, utcnow
from .base import (
    coll,
    count_docs,
    delete_doc,
    find_by_id,
    insert_doc,
    list_docs,
    update_doc,
    valid_oid,
)


async def count_products_by_provider(db: AsyncIOMotorDatabase, provider_id: str) -> int:
    oid = valid_oid(provider_id)
    if oid is None:
        return 0
    return await count_docs(coll(db, "products"), {"provider_id": oid})


async def list_providers(
    db: AsyncIOMotorDatabase,
    *,
    search: str | None = None,
    active_only: bool = False,
) -> list[Provider]:
    query: dict = {}
    if active_only:
        query["active"] = True
    if search:
        query["name"] = {"$regex": re.escape(search), "$options": "i"}
    docs = await list_docs(coll(db, "providers"), query, sort=[("name", 1)])
    return [p for p in (doc_to_model(Provider, d) for d in docs) if p is not None]


async def get_provider(db: AsyncIOMotorDatabase, provider_id: str) -> Provider | None:
    oid = valid_oid(provider_id)
    if oid is None:
        return None
    return await find_by_id(coll(db, "providers"), Provider, oid)


async def create_provider(db: AsyncIOMotorDatabase, data: dict) -> Provider:
    provider_id = await insert_doc(coll(db, "providers"), data)
    provider = await get_provider(db, provider_id)
    assert provider is not None
    return provider


async def update_provider(db: AsyncIOMotorDatabase, provider_id: str, updates: dict) -> bool:
    oid = valid_oid(provider_id)
    if oid is None:
        return False
    return await update_doc(coll(db, "providers"), oid, updates)


async def delete_provider(db: AsyncIOMotorDatabase, provider_id: str) -> bool:
    oid = valid_oid(provider_id)
    if oid is None:
        return False
    return await delete_doc(coll(db, "providers"), oid)


async def list_products(
    db: AsyncIOMotorDatabase,
    *,
    search: str | None = None,
    category: str | None = None,
    provider_id: str | None = None,
    active_only: bool = True,
) -> list[Product]:
    query: dict = {}
    if active_only:
        query["active"] = True
    if search:
        pattern = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]
    if category:
        query["category"] = {"$regex": re.escape(category), "$options": "i"}
    if provider_id:
        oid = valid_oid(provider_id)
        if oid is None:
            return []
        query["provider_id"] = oid
    docs = await list_docs(coll(db, "products"), query, sort=[("name", 1)])
    return [p for p in (doc_to_model(Product, d) for d in docs) if p is not None]


async def get_product(db: AsyncIOMotorDatabase, product_id: str) -> Product | None:
    oid = valid_oid(product_id)
    if oid is None:
        return None
    return await find_by_id(coll(db, "products"), Product, oid)


async def create_product(db: AsyncIOMotorDatabase, data: dict) -> Product:
    product_id = await insert_doc(coll(db, "products"), data)
    product = await get_product(db, product_id)
    assert product is not None
    return product


async def update_product(
    db: AsyncIOMotorDatabase, product_id: str, updates: dict
) -> Product | None:
    oid = valid_oid(product_id)
    if oid is None:
        return None
    await update_doc(coll(db, "products"), oid, updates)
    return await get_product(db, product_id)


async def delete_product(db: AsyncIOMotorDatabase, product_id: str) -> bool:
    oid = valid_oid(product_id)
    if oid is None:
        return False
    return await delete_doc(coll(db, "products"), oid)


async def adjust_stock_atomic(
    db: AsyncIOMotorDatabase,
    product_id: str,
    delta: int,
    *,
    require_stock: bool,
) -> Product | None:
    oid = valid_oid(product_id)
    if oid is None:
        return None
    query: dict = {"_id": oid}
    if delta < 0 and require_stock:
        query["stock"] = {"$gte": -delta}
    result = await coll(db, "products").find_one_and_update(
        query,
        {"$inc": {"stock": delta}, "$set": {"updated_at": utcnow()}},
        return_document=ReturnDocument.AFTER,
    )
    return doc_to_model(Product, result)

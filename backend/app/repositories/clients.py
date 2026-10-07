import re

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Client, doc_to_model
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


async def list_clients(
    db: AsyncIOMotorDatabase,
    *,
    search: str | None = None,
    client_type: str | None = None,
) -> list[Client]:
    query: dict = {}
    if search:
        pattern = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"phone": {"$regex": pattern, "$options": "i"}},
            {"instagram": {"$regex": pattern, "$options": "i"}},
        ]
    if client_type:
        query["type"] = client_type
    docs = await list_docs(coll(db, "clients"), query, sort=[("name", 1)])
    return [c for c in (doc_to_model(Client, d) for d in docs) if c is not None]


async def get_client(db: AsyncIOMotorDatabase, client_id: str) -> Client | None:
    oid = valid_oid(client_id)
    if oid is None:
        return None
    return await find_by_id(coll(db, "clients"), Client, oid)


async def create_client(db: AsyncIOMotorDatabase, data: dict) -> Client:
    client_id = await insert_doc(coll(db, "clients"), data)
    client = await get_client(db, client_id)
    assert client is not None
    return client


async def update_client(db: AsyncIOMotorDatabase, client_id: str, updates: dict) -> bool:
    oid = valid_oid(client_id)
    if oid is None:
        return False
    return await update_doc(coll(db, "clients"), oid, updates)


async def delete_client(db: AsyncIOMotorDatabase, client_id: str) -> bool:
    oid = valid_oid(client_id)
    if oid is None:
        return False
    return await delete_doc(coll(db, "clients"), oid)


async def count_sales_by_client(db: AsyncIOMotorDatabase, client_id: str) -> int:
    oid = valid_oid(client_id)
    if oid is None:
        return 0
    return await count_docs(coll(db, "sales"), {"client_id": oid})

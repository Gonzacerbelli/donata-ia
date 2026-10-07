import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Sale, doc_to_model, to_mongo
from .base import coll, find_by_id, insert_doc, list_docs, count_docs, valid_oid


def _to_oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, ValueError):
        return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


async def list_sales(
    db: AsyncIOMotorDatabase,
    *,
    status: str | None = None,
    client_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> list[Sale]:
    query: dict = {}
    if status:
        query["status"] = status
    if client_id:
        oid = _to_oid(client_id)
        if oid is None:
            return []
        query["client_id"] = oid
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start or end:
        range_query: dict = {}
        if start:
            range_query["$gte"] = start
        if end:
            range_query["$lte"] = end
        query["date"] = range_query
    if search:
        pattern = {"$regex": re.escape(search), "$options": "i"}
        client_ids = [
            c["_id"]
            for c in await coll(db, "clients").find({"name": pattern}, {"_id": 1}).to_list(None)
        ]
        ors: list[dict] = [{"items.description": pattern}]
        if client_ids:
            ors.append({"client_id": {"$in": client_ids}})
        query["$or"] = ors
    docs = await list_docs(coll(db, "sales"), query, sort=[("date", -1)])
    return [s for s in (doc_to_model(Sale, d) for d in docs) if s is not None]


async def get_sale(db: AsyncIOMotorDatabase, sale_id: str) -> Sale | None:
    oid = _to_oid(sale_id)
    if oid is None:
        return None
    return await find_by_id(coll(db, "sales"), Sale, oid)


async def get_sale_doc(db: AsyncIOMotorDatabase, sale_id: str) -> dict | None:
    oid = _to_oid(sale_id)
    if oid is None:
        return None
    return await coll(db, "sales").find_one({"_id": oid})


async def create_sale(db: AsyncIOMotorDatabase, data: dict) -> Sale:
    sale_id = await insert_doc(coll(db, "sales"), data)
    sale = await get_sale(db, sale_id)
    assert sale is not None
    return sale


async def update_sale(db: AsyncIOMotorDatabase, sale_id: str, updates: dict) -> Sale | None:
    oid = _to_oid(sale_id)
    if oid is None:
        return None
    await coll(db, "sales").update_one({"_id": oid}, {"$set": updates})
    return await get_sale(db, sale_id)


async def add_payment(db: AsyncIOMotorDatabase, sale_id: str, payment: dict) -> Sale | None:
    oid = _to_oid(sale_id)
    if oid is None:
        return None
    await coll(db, "sales").update_one(
        {"_id": oid},
        {"$push": {"payments": payment}, "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return await get_sale(db, sale_id)


async def delete_sale(db: AsyncIOMotorDatabase, sale_id: str) -> bool:
    oid = _to_oid(sale_id)
    if oid is None:
        return False
    result = await coll(db, "sales").delete_one({"_id": oid})
    return result.deleted_count > 0


async def count_sales(db: AsyncIOMotorDatabase, query: dict) -> int:
    return await count_docs(coll(db, "sales"), query)
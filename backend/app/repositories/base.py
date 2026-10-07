from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from ..models.base import M, doc_to_model


def valid_oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, ValueError):
        return None


async def find_by_id(coll: AsyncIOMotorCollection, model: type[M], oid: ObjectId) -> M | None:
    doc = await coll.find_one({"_id": oid})
    return doc_to_model(model, doc)


async def find_one_doc(coll: AsyncIOMotorCollection, query: dict) -> dict | None:
    return await coll.find_one(query)


async def list_docs(
    coll: AsyncIOMotorCollection,
    query: dict,
    *,
    sort: list[tuple] | None = None,
    limit: int | None = None,
) -> list[dict]:
    cursor = coll.find(query)
    if sort:
        cursor = cursor.sort(sort)
    if limit is not None:
        cursor = cursor.limit(limit)
    return await cursor.to_list(None)


async def insert_doc(coll: AsyncIOMotorCollection, data: dict) -> str:
    result = await coll.insert_one(data)
    return str(result.inserted_id)


async def update_doc(coll: AsyncIOMotorCollection, oid: ObjectId, updates: dict) -> bool:
    result = await coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0


async def delete_doc(coll: AsyncIOMotorCollection, oid: ObjectId) -> bool:
    result = await coll.delete_one({"_id": oid})
    return result.deleted_count > 0


async def count_docs(coll: AsyncIOMotorCollection, query: dict) -> int:
    return await coll.count_documents(query)


def get_collection(db: AsyncIOMotorDatabase, name: str) -> AsyncIOMotorCollection:
    return db[name]


def coll(db: AsyncIOMotorDatabase, name: str) -> AsyncIOMotorCollection:
    return get_collection(db, name)
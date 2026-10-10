from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import WorkItem, doc_to_model, utcnow
from .base import coll, find_one_doc, valid_oid


async def get_by_sale(db: AsyncIOMotorDatabase, sale_id: str) -> WorkItem | None:
    oid = valid_oid(sale_id)
    if oid is None:
        return None
    doc = await find_one_doc(coll(db, "work_items"), {"sale_id": oid})
    return doc_to_model(WorkItem, doc)


async def upsert(db: AsyncIOMotorDatabase, sale_id: str, updates: dict) -> WorkItem | None:
    oid = valid_oid(sale_id)
    if oid is None:
        return None
    now = utcnow()
    set_fields = dict(updates)
    set_fields["updated_at"] = now
    set_on_insert = {
        "sale_id": oid,
        "status": "pendiente",
        "priority": "media",
        "comments": [],
        "created_at": now,
    }
    for key in set_fields:
        set_on_insert.pop(key, None)
    await coll(db, "work_items").update_one(
        {"sale_id": oid},
        {"$set": set_fields, "$setOnInsert": set_on_insert},
        upsert=True,
    )
    return await get_by_sale(db, sale_id)


async def add_comment(db: AsyncIOMotorDatabase, sale_id: str, comment: dict) -> WorkItem | None:
    oid = valid_oid(sale_id)
    if oid is None:
        return None
    now = utcnow()
    await coll(db, "work_items").update_one(
        {"sale_id": oid},
        {
            "$push": {"comments": comment},
            "$set": {"updated_at": now},
            "$setOnInsert": {
                "sale_id": oid,
                "status": "pendiente",
                "priority": "media",
                "created_at": now,
            },
        },
        upsert=True,
    )
    return await get_by_sale(db, sale_id)


async def list_board(
    db: AsyncIOMotorDatabase,
    *,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    date_sort: str | None = None,
) -> list[dict]:
    pipeline: list[dict] = [
        {"$match": {"status": {"$nin": ["cancelado", "entregado"]}}},
        {
            "$lookup": {
                "from": "work_items",
                "localField": "_id",
                "foreignField": "sale_id",
                "as": "work",
            }
        },
        {"$unwind": {"path": "$work", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "work_status": {"$ifNull": ["$work.status", "pendiente"]},
                "work_priority": {"$ifNull": ["$work.priority", "media"]},
                "work_assigned_to": {"$ifNull": ["$work.assigned_to", None]},
                "work_comments": {"$ifNull": ["$work.comments", []]},
            }
        },
    ]
    if status:
        pipeline.append({"$match": {"work_status": status}})
    if priority:
        pipeline.append({"$match": {"work_priority": priority}})
    if assigned_to:
        oid = valid_oid(assigned_to)
        if oid is None:
            return []
        pipeline.append({"$match": {"work_assigned_to": oid}})
    direction = 1 if (date_sort or "desc").lower() == "asc" else -1
    pipeline.append({"$sort": {"date": direction}})
    cursor = coll(db, "sales").aggregate(pipeline)
    return await cursor.to_list(None)

from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from .base import coll


def _date_range(start: datetime | None, end: datetime | None) -> dict:
    if start and start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    query: dict = {}
    if start:
        query["$gte"] = start
    if end:
        query["$lte"] = end
    return query


async def sales_summary(
    db: AsyncIOMotorDatabase,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    match: dict = {"status": {"$ne": "cancelado"}}
    date_query = _date_range(start, end)
    if date_query:
        match["date"] = date_query
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "sales_count": {"$sum": 1},
                "revenue": {"$sum": "$total"},
                "collected": {"$sum": {"$sum": "$payments.amount"}},
            }
        },
    ]
    result = await coll(db, "sales").aggregate(pipeline).to_list(1)
    return result[0] if result else {"sales_count": 0, "revenue": 0, "collected": 0}


async def top_products(
    db: AsyncIOMotorDatabase,
    limit: int = 5,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    match: dict = {"status": {"$ne": "cancelado"}}
    date_query = _date_range(start, end)
    if date_query:
        match["date"] = date_query
    pipeline = [
        {"$match": match},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.description",
                "qty": {"$sum": "$items.qty"},
                "revenue": {"$sum": {"$multiply": ["$items.qty", "$items.unit_price"]}},
            }
        },
        {"$sort": {"qty": -1}},
        {"$limit": limit},
    ]
    return await coll(db, "sales").aggregate(pipeline).to_list(limit)


async def low_stock_products(db: AsyncIOMotorDatabase) -> list[dict]:
    query = {
        "active": True,
        "$expr": {"$lte": ["$stock", "$min_stock"]},
    }
    cursor = coll(db, "products").find(query).sort("stock", 1)
    return await cursor.to_list(None)


async def inventory_value(db: AsyncIOMotorDatabase) -> dict:
    pipeline = [
        {"$match": {"active": True}},
        {
            "$group": {
                "_id": None,
                "inventory_value": {
                    "$sum": {"$multiply": [{"$ifNull": ["$stock", 0]}, {"$ifNull": ["$cost", 0]}]}
                },
                "units": {"$sum": {"$ifNull": ["$stock", 0]}},
            }
        },
    ]
    result = await coll(db, "products").aggregate(pipeline).to_list(1)
    return result[0] if result else {"inventory_value": 0, "units": 0}

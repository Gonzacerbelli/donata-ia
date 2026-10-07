from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import utcnow
from .base import coll


async def get_states(db: AsyncIOMotorDatabase, user_id: str) -> dict[str, dict]:
    cursor = coll(db, "notification_states").find({"user_id": str(user_id)})
    docs = await cursor.to_list(None)
    return {doc["key"]: doc for doc in docs}


async def set_state(db: AsyncIOMotorDatabase, user_id: str, key: str, **fields: bool) -> None:
    await coll(db, "notification_states").update_one(
        {"user_id": str(user_id), "key": key},
        {"$set": {**fields, "updated_at": utcnow()}},
        upsert=True,
    )


async def set_many(db: AsyncIOMotorDatabase, user_id: str, keys: list[str], **fields: bool) -> None:
    for key in keys:
        await set_state(db, user_id, key, **fields)

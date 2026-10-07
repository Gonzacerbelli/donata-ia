from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel

from .config import settings

_client: AsyncIOMotorClient | None = None

INDEXES: dict[str, list[dict]] = {
    "users": [
        {"keys": [("google_sub", 1)], "unique": True},
        {"keys": [("email", 1)]},
    ],
    "providers": [{"keys": [("name", 1)]}],
    "products": [
        {"keys": [("name", 1)]},
        {"keys": [("provider_id", 1)]},
    ],
    "clients": [{"keys": [("name", 1)]}],
    "sales": [
        {"keys": [("client_id", 1)]},
        {"keys": [("status", 1)]},
        {"keys": [("date", -1)]},
    ],
    "stock_moves": [
        {"keys": [("product_id", 1)]},
        {"keys": [("created_at", -1)]},
        {"keys": [("ref_id", 1)]},
    ],
    "chat_threads": [
        {"keys": [("thread_id", 1)], "unique": True},
        {"keys": [("user_id", 1)]},
    ],
    "chat_messages": [
        {"keys": [("thread_id", 1)]},
        {"keys": [("created_at", 1)]},
    ],
    "notification_states": [
        {"keys": [("user_id", 1), ("key", 1)], "unique": True},
        {"keys": [("user_id", 1)]},
    ],
}


async def connect_db() -> None:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def get_db() -> AsyncIOMotorDatabase:
    if _client is None:
        await connect_db()
    assert _client is not None
    return _client[settings.mongo_db]


def get_test_db(database_name: str) -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("DB client not connected. Call connect_db() first.")
    return _client[database_name]


async def init_indexes(database: AsyncIOMotorDatabase | None = None) -> None:
    db = database or await get_db()
    for name, specs in INDEXES.items():
        await db[name].create_indexes(
            [IndexModel(spec["keys"], unique=spec.get("unique", False)) for spec in specs]
        )


async def ping() -> bool:
    db = await get_db()
    try:
        await db.command("ping")
        return True
    except Exception:
        return False

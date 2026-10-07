import httpx
import pytest_asyncio

from app.config import settings
from app.db import close_db, connect_db, get_db, init_indexes
from app.main import app


@pytest_asyncio.fixture
async def db():
    settings.mongo_db = settings.mongo_db_test
    await connect_db()
    await init_indexes()
    database = await get_db()
    for name in await database.list_collection_names():
        await database[name].delete_many({})
    yield database
    await close_db()


@pytest_asyncio.fixture
async def client(db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client

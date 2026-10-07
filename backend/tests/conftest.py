import httpx
import pytest_asyncio

from app.config import settings
from app.core.security import create_access_token
from app.db import close_db, connect_db, get_db, init_indexes
from app.main import app
from app.models import utcnow
from app.repositories import users as users_repo


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


@pytest_asyncio.fixture
async def user(db):
    return await users_repo.create_user(
        db,
        {
            "google_sub": "test-sub",
            "email": "test@x.com",
            "name": "Test",
            "active": True,
            "created_at": utcnow(),
        },
    )


@pytest_asyncio.fixture
async def auth_client(client, user):
    token = create_access_token(user.id, email=user.email)
    client.headers["Authorization"] = f"Bearer {token}"
    yield client

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import User, doc_to_model, utcnow
from .base import coll, find_by_id, insert_doc, update_doc, valid_oid


async def get_user(db: AsyncIOMotorDatabase, user_id: str) -> User | None:
    oid = valid_oid(user_id)
    if oid is None:
        return None
    return await find_by_id(coll(db, "users"), User, oid)


async def find_user_by_sub(db: AsyncIOMotorDatabase, google_sub: str) -> User | None:
    doc = await coll(db, "users").find_one({"google_sub": google_sub})
    return doc_to_model(User, doc)


async def find_user_by_email(db: AsyncIOMotorDatabase, email: str) -> User | None:
    doc = await coll(db, "users").find_one({"email": email})
    return doc_to_model(User, doc)


async def create_user(db: AsyncIOMotorDatabase, data: dict) -> User:
    user_id = await insert_doc(coll(db, "users"), data)
    user = await get_user(db, user_id)
    assert user is not None
    return user


async def touch_login(db: AsyncIOMotorDatabase, user_id: str) -> None:
    oid = valid_oid(user_id)
    if oid is None:
        return
    await update_doc(coll(db, "users"), oid, {"last_login_at": utcnow()})

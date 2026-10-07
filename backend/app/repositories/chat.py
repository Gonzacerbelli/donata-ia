from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import ChatMessage, ChatThread, doc_to_model, utcnow
from .base import coll, delete_doc, insert_doc, list_docs, update_doc


async def get_thread_by_thread_id(
    db: AsyncIOMotorDatabase, thread_id: str
) -> ChatThread | None:
    doc = await coll(db, "chat_threads").find_one({"thread_id": thread_id})
    return doc_to_model(ChatThread, doc)


async def get_thread_by_id(db: AsyncIOMotorDatabase, pk: str) -> ChatThread | None:
    doc = await coll(db, "chat_threads").find_one({"_id": pk})
    return doc_to_model(ChatThread, doc)


async def list_threads(
    db: AsyncIOMotorDatabase, user_id: str, *, limit: int = 50
) -> list[ChatThread]:
    docs = await list_docs(
        coll(db, "chat_threads"),
        {"user_id": user_id},
        sort=[("updated_at", -1)],
        limit=limit,
    )
    return [t for t in (doc_to_model(ChatThread, d) for d in docs) if t is not None]


async def create_thread(db: AsyncIOMotorDatabase, data: dict) -> ChatThread:
    await insert_doc(coll(db, "chat_threads"), data)
    thread = await get_thread_by_thread_id(db, data["thread_id"])
    assert thread is not None
    return thread


async def touch_thread(db: AsyncIOMotorDatabase, thread_id: str) -> None:
    await coll(db, "chat_threads").update_one(
        {"thread_id": thread_id}, {"$set": {"updated_at": utcnow()}}
    )


async def update_thread_title(
    db: AsyncIOMotorDatabase, thread_id: str, title: str
) -> bool:
    result = await coll(db, "chat_threads").update_one(
        {"thread_id": thread_id}, {"$set": {"title": title, "updated_at": utcnow()}}
    )
    return result.modified_count > 0


async def delete_thread(db: AsyncIOMotorDatabase, thread_id: str) -> bool:
    thread_result = await coll(db, "chat_threads").delete_one({"thread_id": thread_id})
    await coll(db, "chat_messages").delete_many({"thread_id": thread_id})
    return thread_result.deleted_count > 0


async def insert_message(db: AsyncIOMotorDatabase, message: dict) -> ChatMessage:
    await insert_doc(coll(db, "chat_messages"), message)
    return ChatMessage.model_validate(message)


async def list_messages(
    db: AsyncIOMotorDatabase, thread_id: str, *, limit: int = 50
) -> list[ChatMessage]:
    docs = await list_docs(
        coll(db, "chat_messages"),
        {"thread_id": thread_id},
        sort=[("created_at", -1)],
        limit=limit,
    )
    docs.reverse()
    return [m for m in (doc_to_model(ChatMessage, d) for d in docs) if m is not None]
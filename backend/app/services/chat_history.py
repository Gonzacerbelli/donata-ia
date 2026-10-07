from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import NotFoundError
from ..models import ChatMessage, ChatThread, utcnow
from ..repositories import chat as chat_repo


async def list_threads(
    db: AsyncIOMotorDatabase, user_id: str, *, limit: int = 50
) -> list[ChatThread]:
    return await chat_repo.list_threads(db, user_id, limit=limit)


async def get_thread_or_404(db: AsyncIOMotorDatabase, user_id: str, thread_id: str) -> ChatThread:
    thread = await chat_repo.get_thread_by_thread_id(db, thread_id)
    if thread is None or str(thread.user_id) != str(user_id):
        raise NotFoundError("La conversación no existe")
    return thread


async def create_thread(
    db: AsyncIOMotorDatabase, user_id: str, thread_id: str, title: str | None = None
) -> ChatThread:
    existing = await chat_repo.get_thread_by_thread_id(db, thread_id)
    if existing is not None:
        if str(existing.user_id) != str(user_id):
            raise NotFoundError("La conversación no existe")
        return existing
    return await chat_repo.create_thread(
        db,
        {
            "thread_id": thread_id,
            "user_id": str(user_id),
            "title": title or "Nueva conversación",
            "created_at": utcnow(),
            "updated_at": utcnow(),
        },
    )


async def rename_thread(
    db: AsyncIOMotorDatabase, user_id: str, thread_id: str, title: str
) -> ChatThread:
    await get_thread_or_404(db, user_id, thread_id)
    await chat_repo.update_thread_title(db, thread_id, title)
    thread = await chat_repo.get_thread_by_thread_id(db, thread_id)
    assert thread is not None
    return thread


async def delete_thread(db: AsyncIOMotorDatabase, user_id: str, thread_id: str) -> None:
    await get_thread_or_404(db, user_id, thread_id)
    await chat_repo.delete_thread(db, thread_id)


async def list_messages(
    db: AsyncIOMotorDatabase, user_id: str, thread_id: str, *, limit: int = 50
) -> list[ChatMessage]:
    await get_thread_or_404(db, user_id, thread_id)
    return await chat_repo.list_messages(db, thread_id, limit=limit)


async def append_message(
    db: AsyncIOMotorDatabase,
    thread_id: str,
    role: str,
    content: str,
    *,
    tool_calls: list[dict] | None = None,
) -> ChatMessage:
    message = await chat_repo.insert_message(
        db,
        {
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
            "created_at": utcnow(),
        },
    )
    await chat_repo.touch_thread(db, thread_id)
    return message

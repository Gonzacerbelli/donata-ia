from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, Database, get_current_user
from ..schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatThreadCreate,
    ChatThreadOut,
    ChatThreadUpdate,
)
from ..services import chat_history as chat_service
from ..services.llm import assistant

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, user: CurrentUser, db: Database) -> ChatResponse:
    result = await assistant.handle_message(db, str(user.id), body.thread_id, body.message)
    return ChatResponse(**result)


@router.get("/threads", response_model=list[ChatThreadOut])
async def list_threads(user: CurrentUser, db: Database) -> list[ChatThreadOut]:
    threads = await chat_service.list_threads(db, str(user.id))
    return [ChatThreadOut.model_validate(t.model_dump()) for t in threads]


@router.post("/threads", response_model=ChatThreadOut, status_code=201)
async def create_thread(body: ChatThreadCreate, user: CurrentUser, db: Database) -> ChatThreadOut:
    thread = await chat_service.create_thread(db, str(user.id), body.thread_id, body.title)
    return ChatThreadOut.model_validate(thread.model_dump())


@router.patch("/threads/{thread_id}", response_model=ChatThreadOut)
async def rename_thread(
    thread_id: str, body: ChatThreadUpdate, user: CurrentUser, db: Database
) -> ChatThreadOut:
    title = body.title or "Nueva conversación"
    thread = await chat_service.rename_thread(db, str(user.id), thread_id, title)
    return ChatThreadOut.model_validate(thread.model_dump())


@router.delete("/threads/{thread_id}", status_code=204)
async def delete_thread(thread_id: str, user: CurrentUser, db: Database) -> None:
    await chat_service.delete_thread(db, str(user.id), thread_id)


@router.get("/threads/{thread_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(thread_id: str, user: CurrentUser, db: Database) -> list[ChatMessageOut]:
    messages = await chat_service.list_messages(db, str(user.id), thread_id)
    return [ChatMessageOut.model_validate(m.model_dump()) for m in messages]

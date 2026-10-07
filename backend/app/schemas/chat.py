from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from ..models.base import ObjIdStr


class ChatMessageOut(BaseModel):
    id: str
    thread_id: str
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[dict] = Field(default_factory=list)
    created_at: datetime


class ChatThreadOut(BaseModel):
    id: str
    thread_id: str
    user_id: ObjIdStr
    title: str
    created_at: datetime
    updated_at: datetime


class ChatThreadCreate(BaseModel):
    thread_id: str = Field(min_length=1, max_length=80)
    title: str | None = Field(default=None, max_length=160)


class ChatThreadUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    thread_id: str
    tool_calls: list[dict] = Field(default_factory=list)
    response: str

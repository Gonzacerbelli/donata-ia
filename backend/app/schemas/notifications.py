from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    type: str
    severity: Literal["alta", "media", "baja"]
    title: str
    description: str
    entity: Literal["product", "sale"]
    entity_id: str
    action: str | None = None
    read: bool = False
    dismissed: bool = False
    created_at: datetime | None = None


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class NotificationUpdate(BaseModel):
    read: bool | None = None
    dismissed: bool | None = None

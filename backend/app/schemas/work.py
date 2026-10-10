from datetime import datetime

from pydantic import BaseModel

from ..models.domain import SaleItem, WorkComment, WorkPriority, WorkStatus


class WorkCard(BaseModel):
    sale_id: str
    client_id: str
    date: datetime
    items: list[SaleItem]
    total: int
    status: WorkStatus
    priority: WorkPriority
    assigned_to: str | None = None
    comments: list[WorkComment] = []

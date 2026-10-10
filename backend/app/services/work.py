from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import NotFoundError, UnprocessableError
from ..models import Sale, User, utcnow
from ..repositories import sales as sales_repo
from ..repositories import users as users_repo
from ..repositories import work_items as work_repo
from ..repositories.base import valid_oid
from ..schemas.entities import WorkItemUpdate
from ..schemas.work import WorkCard


def _card(sale: Sale, item) -> WorkCard:
    return WorkCard(
        sale_id=str(sale.id),
        client_id=str(sale.client_id),
        date=sale.date,
        items=sale.items,
        total=sale.total,
        status=item.status,
        priority=item.priority,
        assigned_to=str(item.assigned_to) if item.assigned_to else None,
        comments=item.comments,
    )


def _card_from_doc(doc: dict) -> WorkCard:
    return WorkCard(
        sale_id=str(doc["_id"]),
        client_id=str(doc["client_id"]) if doc.get("client_id") else "",
        date=doc["date"],
        items=doc.get("items", []),
        total=doc.get("total", 0),
        status=doc.get("work_status", "pendiente"),
        priority=doc.get("work_priority", "media"),
        assigned_to=str(doc["work_assigned_to"]) if doc.get("work_assigned_to") else None,
        comments=doc.get("work_comments", []),
    )


async def _get_open_sale(db: AsyncIOMotorDatabase, sale_id: str) -> Sale:
    sale = await sales_repo.get_sale(db, sale_id)
    if sale is None or sale.status in ("cancelado", "entregado"):
        raise NotFoundError("La tarjeta de trabajo no existe")
    return sale


async def mark_delivered(db: AsyncIOMotorDatabase, sale_id: str) -> None:
    await work_repo.upsert(db, sale_id, {"status": "terminado"})


async def mark_reopened(db: AsyncIOMotorDatabase, sale_id: str) -> None:
    await work_repo.upsert(db, sale_id, {"status": "pendiente"})


async def list_board(
    db: AsyncIOMotorDatabase,
    *,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    date_sort: str | None = None,
) -> list[WorkCard]:
    docs = await work_repo.list_board(
        db,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        date_sort=date_sort,
    )
    return [_card_from_doc(doc) for doc in docs]


async def update_work(db: AsyncIOMotorDatabase, sale_id: str, body: WorkItemUpdate) -> WorkCard:
    sale = await _get_open_sale(db, sale_id)
    updates = body.model_dump(exclude_unset=True)
    if updates.get("assigned_to") is not None:
        target = await users_repo.get_user(db, str(updates["assigned_to"]))
        if target is None or not target.active:
            raise UnprocessableError("El usuario asignado no existe o est� inactivo")
        updates["assigned_to"] = valid_oid(str(updates["assigned_to"]))
    item = await work_repo.upsert(db, sale_id, updates)
    assert item is not None
    return _card(sale, item)


async def add_comment(db: AsyncIOMotorDatabase, sale_id: str, text: str, author: User) -> WorkCard:
    sale = await _get_open_sale(db, sale_id)
    comment = {
        "id": uuid4().hex,
        "author_id": valid_oid(str(author.id)),
        "author_name": author.name or author.email,
        "text": text,
        "created_at": utcnow(),
    }
    item = await work_repo.add_comment(db, sale_id, comment)
    assert item is not None
    return _card(sale, item)

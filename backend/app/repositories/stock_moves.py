from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import StockMove, doc_to_model
from .base import coll, insert_doc, list_docs, valid_oid


async def record_move(db: AsyncIOMotorDatabase, move: dict) -> None:
    await insert_doc(coll(db, "stock_moves"), move)


async def list_moves(
    db: AsyncIOMotorDatabase,
    product_id: str | None = None,
    *,
    limit: int | None = None,
) -> list[StockMove]:
    query: dict = {}
    if product_id:
        oid = valid_oid(product_id)
        if oid is None:
            return []
        query["product_id"] = oid
    docs = await list_docs(coll(db, "stock_moves"), query, sort=[("created_at", -1)], limit=limit)
    return [m for m in (doc_to_model(StockMove, d) for d in docs) if m is not None]

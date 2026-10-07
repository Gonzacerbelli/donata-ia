from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Product, doc_to_model
from ..repositories import reports as reports_repo


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


async def sales_summary(
    db: AsyncIOMotorDatabase, *, date_from: str | None = None, date_to: str | None = None
) -> dict:
    data = await reports_repo.sales_summary(db, _parse(date_from), _parse(date_to))
    revenue = data.get("revenue") or 0
    collected = data.get("collected") or 0
    count = data.get("sales_count") or 0
    return {
        "sales_count": count,
        "revenue": revenue,
        "collected": collected,
        "receivable": revenue - collected,
        "average_ticket": round(revenue / count) if count else 0,
    }


async def top_products(
    db: AsyncIOMotorDatabase,
    *,
    limit: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    rows = await reports_repo.top_products(db, limit, _parse(date_from), _parse(date_to))
    return [
        {"description": row["_id"], "qty": row["qty"], "revenue": row["revenue"]} for row in rows
    ]


async def low_stock(db: AsyncIOMotorDatabase) -> list[Product]:
    docs = await reports_repo.low_stock_products(db)
    return [p for p in (doc_to_model(Product, d) for d in docs) if p is not None]


async def inventory_value(db: AsyncIOMotorDatabase) -> dict:
    data = await reports_repo.inventory_value(db)
    return {
        "inventory_value": data.get("inventory_value") or 0,
        "units": data.get("units") or 0,
    }

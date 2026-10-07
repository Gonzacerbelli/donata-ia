from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..models import Product
from ..services import reports as reports_service

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
async def sales_summary(
    db: Database,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    return await reports_service.sales_summary(db, date_from=date_from, date_to=date_to)


@router.get("/top-products")
async def top_products(
    db: Database,
    limit: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    return await reports_service.top_products(db, limit=limit, date_from=date_from, date_to=date_to)


@router.get("/low-stock", response_model=list[Product])
async def low_stock(db: Database) -> list[Product]:
    return await reports_service.low_stock(db)


@router.get("/inventory-value")
async def inventory_value(db: Database) -> dict:
    return await reports_service.inventory_value(db)

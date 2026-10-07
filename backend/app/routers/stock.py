from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..services import stock as stock_service

router = APIRouter(prefix="/stock", tags=["stock"], dependencies=[Depends(get_current_user)])


@router.get("/moves")
async def list_moves(db: Database, product_id: str | None = None, limit: int = 100) -> list:
    return await stock_service.list_moves(db, product_id, limit=limit)

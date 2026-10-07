from fastapi import APIRouter, Depends, Query

from ..dependencies import Database, get_current_user
from ..models import Product
from ..schemas.entities import ProductCreate, ProductUpdate, StockAdjust
from ..services import products as products_service
from ..services import stock as stock_service

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[Product])
async def list_products(
    db: Database,
    search: str | None = None,
    category: str | None = None,
    provider_id: str | None = None,
    active_only: bool = True,
) -> list[Product]:
    return await products_service.list_products(
        db, search=search, category=category, provider_id=provider_id, active_only=active_only
    )


@router.post("", response_model=Product, status_code=201)
async def create_product(body: ProductCreate, db: Database) -> Product:
    return await products_service.create_product(db, body)


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str, db: Database) -> Product:
    return await products_service.get_product_or_404(db, product_id)


@router.patch("/{product_id}", response_model=Product)
async def update_product(product_id: str, body: ProductUpdate, db: Database) -> Product:
    return await products_service.update_product(db, product_id, body)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str, db: Database) -> None:
    await products_service.delete_product(db, product_id)


@router.post("/stock/adjust", response_model=Product)
async def adjust_stock(body: StockAdjust, db: Database) -> Product:
    return await stock_service.adjust_stock(db, body.product_id, body.quantity, body.reason)


@router.get("/{product_id}/moves")
async def product_moves(
    product_id: str,
    db: Database,
    limit: int = Query(default=50, ge=1, le=500),
) -> list:
    return await stock_service.list_moves(db, product_id, limit=limit)

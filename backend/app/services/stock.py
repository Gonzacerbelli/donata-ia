from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import BusinessRuleError, NotFoundError
from ..models import Product
from ..repositories import products as products_repo
from ..repositories import stock_moves as moves_repo
from ..repositories.base import valid_oid


async def move_stock(
    db: AsyncIOMotorDatabase,
    product_id: str,
    quantity: int,
    *,
    reason: str | None = None,
    ref_type: str | None = None,
    ref_id: str | None = None,
    require_stock: bool = True,
) -> Product:
    product = await products_repo.get_product(db, product_id)
    if product is None:
        raise NotFoundError("El producto no existe")
    updated = await products_repo.adjust_stock_atomic(
        db, product_id, quantity, require_stock=require_stock
    )
    if updated is None:
        raise BusinessRuleError(f"Stock insuficiente para '{product.name}'")
    await moves_repo.record_move(
        db,
        {
            "product_id": valid_oid(product_id),
            "product_name": product.name,
            "quantity": quantity,
            "stock_after": updated.stock,
            "reason": reason,
            "ref_type": ref_type,
            "ref_id": valid_oid(ref_id) if ref_id else None,
        },
    )
    return updated


async def adjust_stock(
    db: AsyncIOMotorDatabase,
    product_id: str,
    quantity: int,
    reason: str,
) -> Product:
    product = await products_repo.get_product(db, product_id)
    if product is None:
        raise NotFoundError("El producto no existe")
    updated = await products_repo.adjust_stock_atomic(db, product_id, quantity, require_stock=False)
    assert updated is not None
    await moves_repo.record_move(
        db,
        {
            "product_id": valid_oid(product_id),
            "product_name": product.name,
            "quantity": quantity,
            "stock_after": updated.stock,
            "reason": reason,
            "ref_type": "ajuste",
            "ref_id": None,
        },
    )
    return updated


async def list_moves(
    db: AsyncIOMotorDatabase, product_id: str | None = None, *, limit: int | None = None
) -> list:
    return await moves_repo.list_moves(db, product_id, limit=limit)

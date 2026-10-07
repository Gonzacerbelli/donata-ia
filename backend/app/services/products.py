from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import ConflictError, NotFoundError, UnprocessableError
from ..models import Product, utcnow
from ..repositories import products as products_repo
from ..repositories import sales as sales_repo
from ..repositories.base import valid_oid
from ..schemas.entities import ProductCreate, ProductUpdate


async def list_products(
    db: AsyncIOMotorDatabase,
    *,
    search: str | None = None,
    category: str | None = None,
    provider_id: str | None = None,
    active_only: bool = True,
) -> list[Product]:
    return await products_repo.list_products(
        db, search=search, category=category, provider_id=provider_id, active_only=active_only
    )


async def get_product_or_404(db: AsyncIOMotorDatabase, product_id: str) -> Product:
    product = await products_repo.get_product(db, product_id)
    if product is None:
        raise NotFoundError("El producto no existe")
    return product


async def _ensure_provider_exists(db: AsyncIOMotorDatabase, provider_id: str) -> None:
    if await products_repo.get_provider(db, provider_id) is None:
        raise UnprocessableError("El proveedor indicado no existe")


async def create_product(db: AsyncIOMotorDatabase, body: ProductCreate) -> Product:
    await _ensure_provider_exists(db, body.provider_id)
    data = body.model_dump()
    data["provider_id"] = valid_oid(body.provider_id)
    data["active"] = True
    data["updated_at"] = utcnow()
    return await products_repo.create_product(db, data)


async def update_product(db: AsyncIOMotorDatabase, product_id: str, body: ProductUpdate) -> Product:
    await get_product_or_404(db, product_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("provider_id"):
        await _ensure_provider_exists(db, data["provider_id"])
        data["provider_id"] = valid_oid(data["provider_id"])
    data["updated_at"] = utcnow()
    updated = await products_repo.update_product(db, product_id, data)
    assert updated is not None
    return updated


async def delete_product(db: AsyncIOMotorDatabase, product_id: str) -> None:
    await get_product_or_404(db, product_id)
    if await sales_repo.count_sales_by_product(db, product_id) > 0:
        raise ConflictError("No se puede eliminar: el producto tiene ventas registradas")
    await products_repo.delete_product(db, product_id)

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import ConflictError, NotFoundError
from ..models import Provider, utcnow
from ..repositories import products as products_repo
from ..schemas.entities import ProviderCreate, ProviderUpdate


async def list_providers(
    db: AsyncIOMotorDatabase, *, search: str | None = None, active_only: bool = False
) -> list[Provider]:
    return await products_repo.list_providers(db, search=search, active_only=active_only)


async def get_provider_or_404(db: AsyncIOMotorDatabase, provider_id: str) -> Provider:
    provider = await products_repo.get_provider(db, provider_id)
    if provider is None:
        raise NotFoundError("El proveedor no existe")
    return provider


async def create_provider(db: AsyncIOMotorDatabase, body: ProviderCreate) -> Provider:
    now = utcnow()
    data = body.model_dump()
    data["active"] = True
    data["created_at"] = now
    data["updated_at"] = now
    return await products_repo.create_provider(db, data)


async def update_provider(
    db: AsyncIOMotorDatabase, provider_id: str, body: ProviderUpdate
) -> Provider:
    await get_provider_or_404(db, provider_id)
    updates = body.model_dump(exclude_none=True)
    if updates:
        updates["updated_at"] = utcnow()
        await products_repo.update_provider(db, provider_id, updates)
    return await get_provider_or_404(db, provider_id)


async def delete_provider(db: AsyncIOMotorDatabase, provider_id: str) -> None:
    await get_provider_or_404(db, provider_id)
    if await products_repo.count_products_by_provider(db, provider_id) > 0:
        raise ConflictError("No se puede eliminar: el proveedor tiene productos asociados")
    await products_repo.delete_provider(db, provider_id)

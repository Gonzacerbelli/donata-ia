from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import ConflictError, NotFoundError
from ..models import Client, utcnow
from ..repositories import clients as clients_repo
from ..schemas.entities import ClientCreate, ClientUpdate


async def list_clients(
    db: AsyncIOMotorDatabase, *, search: str | None = None, client_type: str | None = None
) -> list[Client]:
    return await clients_repo.list_clients(db, search=search, client_type=client_type)


async def get_client_or_404(db: AsyncIOMotorDatabase, client_id: str) -> Client:
    client = await clients_repo.get_client(db, client_id)
    if client is None:
        raise NotFoundError("El cliente no existe")
    return client


async def create_client(db: AsyncIOMotorDatabase, body: ClientCreate) -> Client:
    now = utcnow()
    data = body.model_dump()
    data["created_at"] = now
    data["updated_at"] = now
    return await clients_repo.create_client(db, data)


async def update_client(db: AsyncIOMotorDatabase, client_id: str, body: ClientUpdate) -> Client:
    await get_client_or_404(db, client_id)
    updates = body.model_dump(exclude_unset=True)
    updates["updated_at"] = utcnow()
    await clients_repo.update_client(db, client_id, updates)
    return await get_client_or_404(db, client_id)


async def delete_client(db: AsyncIOMotorDatabase, client_id: str) -> None:
    await get_client_or_404(db, client_id)
    if await clients_repo.count_sales_by_client(db, client_id) > 0:
        raise ConflictError("No se puede eliminar: el cliente tiene ventas registradas")
    await clients_repo.delete_client(db, client_id)

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import ConflictError, NotFoundError
from ..models import Client
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
    return await clients_repo.create_client(db, body.model_dump())


async def update_client(db: AsyncIOMotorDatabase, client_id: str, body: ClientUpdate) -> Client:
    await get_client_or_404(db, client_id)
    await clients_repo.update_client(db, client_id, body.model_dump(exclude_unset=True))
    return await get_client_or_404(db, client_id)


async def delete_client(db: AsyncIOMotorDatabase, client_id: str) -> None:
    await get_client_or_404(db, client_id)
    if await clients_repo.count_sales_by_client(db, client_id) > 0:
        raise ConflictError("No se puede eliminar: el cliente tiene ventas registradas")
    await clients_repo.delete_client(db, client_id)

from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..models import Client
from ..schemas.entities import ClientCreate, ClientUpdate
from ..services import clients as clients_service

router = APIRouter(prefix="/clients", tags=["clients"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[Client])
async def list_clients(
    db: Database,
    search: str | None = None,
    client_type: str | None = None,
) -> list[Client]:
    return await clients_service.list_clients(db, search=search, client_type=client_type)


@router.post("", response_model=Client, status_code=201)
async def create_client(body: ClientCreate, db: Database) -> Client:
    return await clients_service.create_client(db, body)


@router.get("/{client_id}", response_model=Client)
async def get_client(client_id: str, db: Database) -> Client:
    return await clients_service.get_client_or_404(db, client_id)


@router.patch("/{client_id}", response_model=Client)
async def update_client(client_id: str, body: ClientUpdate, db: Database) -> Client:
    return await clients_service.update_client(db, client_id, body)


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: str, db: Database) -> None:
    await clients_service.delete_client(db, client_id)

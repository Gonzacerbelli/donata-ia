from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..models import Provider
from ..schemas.entities import ProviderCreate, ProviderUpdate
from ..services import providers as providers_service

router = APIRouter(
    prefix="/providers", tags=["providers"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[Provider])
async def list_providers(
    db: Database,
    search: str | None = None,
    active_only: bool = False,
) -> list[Provider]:
    return await providers_service.list_providers(db, search=search, active_only=active_only)


@router.post("", response_model=Provider, status_code=201)
async def create_provider(body: ProviderCreate, db: Database) -> Provider:
    return await providers_service.create_provider(db, body)


@router.get("/{provider_id}", response_model=Provider)
async def get_provider(provider_id: str, db: Database) -> Provider:
    return await providers_service.get_provider_or_404(db, provider_id)


@router.patch("/{provider_id}", response_model=Provider)
async def update_provider(provider_id: str, body: ProviderUpdate, db: Database) -> Provider:
    return await providers_service.update_provider(db, provider_id, body)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: str, db: Database) -> None:
    await providers_service.delete_provider(db, provider_id)

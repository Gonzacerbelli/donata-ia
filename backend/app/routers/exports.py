from fastapi import APIRouter, Depends, Response

from ..dependencies import Database, get_current_user
from ..services import exports as exports_service

router = APIRouter(prefix="/exports", tags=["exports"], dependencies=[Depends(get_current_user)])


@router.get("/{entity}.{fmt}")
async def export_entity(
    entity: str,
    fmt: str,
    db: Database,
    status: str | None = None,
    client_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    client_type: str | None = None,
    category: str | None = None,
    provider_id: str | None = None,
    active_only: bool = True,
) -> Response:
    filters = {
        "status": status,
        "client_id": client_id,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
        "client_type": client_type,
        "category": category,
        "provider_id": provider_id,
        "active_only": active_only,
    }
    content, filename, media_type = await exports_service.build_export(db, entity, fmt, filters)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

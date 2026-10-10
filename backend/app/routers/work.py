from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, Database, get_current_user
from ..schemas.entities import CommentCreate, WorkItemUpdate
from ..schemas.work import WorkCard
from ..services import work as work_service

router = APIRouter(prefix="/work-items", tags=["work"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[WorkCard])
async def list_board(
    db: Database,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    date_sort: str | None = None,
) -> list[WorkCard]:
    return await work_service.list_board(
        db,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        date_sort=date_sort,
    )


@router.patch("/{sale_id}", response_model=WorkCard)
async def update_work(sale_id: str, body: WorkItemUpdate, db: Database) -> WorkCard:
    return await work_service.update_work(db, sale_id, body)


@router.post("/{sale_id}/comments", response_model=WorkCard, status_code=201)
async def add_comment(
    sale_id: str, body: CommentCreate, user: CurrentUser, db: Database
) -> WorkCard:
    return await work_service.add_comment(db, sale_id, body.text, user)

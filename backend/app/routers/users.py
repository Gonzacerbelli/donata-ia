from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..repositories import users as users_repo
from ..schemas.auth import UserSummary

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[UserSummary])
async def list_users(db: Database) -> list[UserSummary]:
    users = await users_repo.list_active(db)
    return [UserSummary(id=user.id or "", name=user.name, email=user.email) for user in users]

from typing import Annotated

from fastapi import APIRouter, Query

from ..dependencies import CurrentUser, Database
from ..schemas.auth import GoogleAuthStart, LoginRequest, TokenOut, UserOut, user_to_out
from ..services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google", response_model=GoogleAuthStart)
async def google_start() -> GoogleAuthStart:
    url, _state = auth_service.build_authorize_url()
    return GoogleAuthStart(url=url)


@router.get("/google/callback", response_model=TokenOut)
async def google_callback(
    db: Database,
    code: Annotated[str, Query(min_length=1)],
    state: Annotated[str, Query(min_length=1)],
) -> TokenOut:
    user = await auth_service.authenticate_google_callback(db, code, state)
    return TokenOut(access_token=auth_service.issue_token(user), user=user_to_out(user))


@router.post("/login", response_model=TokenOut)
async def local_login(body: LoginRequest, db: Database) -> TokenOut:
    user = await auth_service.authenticate_local(db, body.username, body.password)
    return TokenOut(access_token=auth_service.issue_token(user), user=user_to_out(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return user_to_out(user)

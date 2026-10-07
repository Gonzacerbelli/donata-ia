from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from ..config import settings
from ..core.errors import DomainError, ForbiddenError, UnauthorizedError
from ..dependencies import CurrentUser, Database
from ..repositories import users as users_repo
from ..schemas.auth import (
    AuthCodeExchange,
    GoogleAuthStart,
    LoginRequest,
    TokenOut,
    UserOut,
    user_to_out,
)
from ..services import auth as auth_service
from ..services import auth_codes

router = APIRouter(prefix="/auth", tags=["auth"])


def _frontend(path: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}{path}"


@router.get("/google", response_model=GoogleAuthStart)
async def google_start() -> GoogleAuthStart:
    url, _state = auth_service.build_authorize_url()
    return GoogleAuthStart(url=url)


@router.get("/google/callback")
async def google_callback(
    db: Database,
    code: Annotated[str | None, Query(min_length=1)] = None,
    state: Annotated[str | None, Query(min_length=1)] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if error or not code or not state:
        return RedirectResponse(
            _frontend(f"/login?error={quote('No se pudo iniciar sesión con Google')}"),
            status_code=302,
        )
    try:
        user = await auth_service.authenticate_google_callback(db, code, state)
    except DomainError as exc:
        return RedirectResponse(_frontend(f"/login?error={quote(exc.message)}"), status_code=302)
    if not user.id:
        return RedirectResponse(
            _frontend(f"/login?error={quote('No se pudo iniciar sesión con Google')}"),
            status_code=302,
        )
    return RedirectResponse(
        _frontend(f"/auth/callback?code={auth_codes.create_auth_code(user.id)}"),
        status_code=302,
    )


@router.post("/exchange", response_model=TokenOut)
async def exchange_auth_code(db: Database, body: AuthCodeExchange) -> TokenOut:
    user_id = auth_codes.pop_auth_code(body.code)
    if not user_id:
        raise UnauthorizedError("El enlace de inicio de sesión ya no es válido o expiró")
    user = await users_repo.get_user(db, user_id)
    if user is None:
        raise UnauthorizedError("El enlace de inicio de sesión ya no es válido")
    if not user.active:
        raise ForbiddenError("Tu usuario está desactivado")
    return TokenOut(access_token=auth_service.issue_token(user), user=user_to_out(user))


@router.post("/login", response_model=TokenOut)
async def local_login(db: Database, body: LoginRequest) -> TokenOut:
    user = await auth_service.authenticate_local(db, body.username, body.password)
    return TokenOut(access_token=auth_service.issue_token(user), user=user_to_out(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return user_to_out(user)

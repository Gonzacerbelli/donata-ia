import logging
from urllib.parse import urlencode

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import settings
from ..core.errors import (
    BusinessRuleError,
    DependencyUnavailableError,
    ForbiddenError,
    UnauthorizedError,
)
from ..core.security import create_access_token, create_oauth_state, verify_oauth_state
from ..models import User, utcnow
from ..repositories import users as users_repo

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPE = "openid email profile"


def build_authorize_url() -> tuple[str, str]:
    state = create_oauth_state()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}", state


async def exchange_code_for_userinfo(code: str) -> dict:
    if not settings.google_client_id or not settings.google_client_secret:
        raise DependencyUnavailableError("Google OAuth no está configurado")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise UnauthorizedError("Google no devolvió un access token")
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            return userinfo_response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("fallo el canje de código con Google: %s", exc)
        raise UnauthorizedError("No se pudo validar la cuenta de Google") from exc
    except httpx.HTTPError as exc:
        logger.error("error de red contactando a Google: %s", exc)
        raise DependencyUnavailableError("Google no está disponible en este momento") from exc


async def upsert_google_user(db: AsyncIOMotorDatabase, userinfo: dict) -> User:
    google_sub = userinfo.get("sub")
    if not google_sub:
        raise UnauthorizedError("La cuenta de Google no devolvió un identificador")
    user = await users_repo.find_user_by_sub(db, google_sub)
    if user is not None:
        if not user.active:
            raise ForbiddenError("Tu usuario está desactivado")
        await users_repo.touch_login(db, user.id or "")
        refreshed = await users_repo.get_user(db, user.id or "")
        return refreshed or user
    created = await users_repo.create_user(
        db,
        {
            "google_sub": google_sub,
            "email": userinfo.get("email", ""),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
            "active": True,
            "created_at": utcnow(),
            "last_login_at": utcnow(),
        },
    )
    return created


async def authenticate_google_callback(db: AsyncIOMotorDatabase, code: str, state: str) -> User:
    if not verify_oauth_state(state):
        raise BusinessRuleError("El estado de OAuth es inválido o expiró")
    userinfo = await exchange_code_for_userinfo(code)
    return await upsert_google_user(db, userinfo)


async def authenticate_local(db: AsyncIOMotorDatabase, username: str, password: str) -> User:
    if not settings.enable_local_login or settings.env == "production":
        raise UnauthorizedError("El login local está deshabilitado")
    if username != settings.local_admin_username or password != settings.local_admin_password:
        raise UnauthorizedError("Usuario o contraseña incorrectos")
    sub = f"local:{username}"
    user = await users_repo.find_user_by_sub(db, sub)
    if user is None:
        user = await users_repo.create_user(
            db,
            {
                "google_sub": sub,
                "email": f"{username}@local",
                "name": username,
                "active": True,
                "created_at": utcnow(),
                "last_login_at": utcnow(),
            },
        )
    else:
        await users_repo.touch_login(db, user.id or "")
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id or "", email=user.email)

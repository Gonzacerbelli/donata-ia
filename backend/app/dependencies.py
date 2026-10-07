from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from .core.errors import ForbiddenError, UnauthorizedError
from .core.security import decode_access_token
from .db import get_db
from .models.domain import User
from .repositories import users as users_repo

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Falta el token de acceso")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Token inválido o expirado")
    user = await users_repo.get_user(db, str(payload.get("sub", "")))
    if user is None:
        raise UnauthorizedError("El usuario no existe")
    if not user.active:
        raise ForbiddenError("El usuario está deshabilitado")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[AsyncIOMotorDatabase, Depends(get_db)]

from datetime import UTC, datetime, timedelta

import jwt

from ..config import settings

OAUTH_STATE_TYPE = "oauth_state"


def create_access_token(
    subject: str,
    *,
    email: str | None = None,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload = {
        "sub": subject,
        "email": email,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None


def create_oauth_state() -> str:
    now = datetime.now(UTC)
    payload = {
        "type": OAUTH_STATE_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_oauth_state(state: str) -> bool:
    payload = decode_access_token(state)
    return bool(payload and payload.get("type") == OAUTH_STATE_TYPE)

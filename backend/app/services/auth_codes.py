import secrets
import time

_TTL_SECONDS = 60
_CODES: dict[str, tuple[str, float]] = {}


def _purge() -> None:
    now = time.time()
    for code in [code for code, (_, exp) in _CODES.items() if exp < now]:
        _CODES.pop(code, None)


def create_auth_code(user_id: str) -> str:
    _purge()
    code = secrets.token_urlsafe(32)
    _CODES[code] = (user_id, time.time() + _TTL_SECONDS)
    return code


def pop_auth_code(code: str) -> str | None:
    _purge()
    entry = _CODES.pop(code, None)
    if entry is None:
        return None
    user_id, expires = entry
    if expires < time.time():
        return None
    return user_id


def reset_auth_codes() -> None:
    _CODES.clear()

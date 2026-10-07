import math
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..config import settings
from ..core.security import decode_access_token

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-XSS-Protection": "0",
}

HSTS_HEADER = {"Strict-Transport-Security": "max-age=31536000; includeSubDomains"}

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

_WINDOW_SECONDS = 60
_WINDOWS: dict[str, list] = {}
_MAX_BODY_BYTES = 2_000_000


def reset_rate_limits() -> None:
    _WINDOWS.clear()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in _WRITE_METHODS and _body_too_large(request):
            return JSONResponse(
                status_code=413,
                content={"detail": "El cuerpo de la petición es demasiado grande."},
            )
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        if settings.env != "dev":
            response.headers.update(HSTS_HEADER)
        return response


def _body_too_large(request) -> bool:
    raw = request.headers.get("content-length", "")
    return raw.isdigit() and int(raw) > _MAX_BODY_BYTES


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        category, limit = _resolve_limit(request.method, request.url.path)
        if limit <= 0:
            return await call_next(request)

        now = time.time()
        window = int(now // _WINDOW_SECONDS)
        key = f"{_identity(request)}:{category}"
        entry = _WINDOWS.get(key)
        if entry is None or entry[0] != window:
            entry = [window, 0]
        entry[1] += 1
        _WINDOWS[key] = entry

        if entry[1] > limit:
            retry_after = max(1, math.ceil(_WINDOW_SECONDS - (now % _WINDOW_SECONDS)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Esperá un momento e intentá de nuevo."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


def _resolve_limit(method: str, path: str) -> tuple[str, int]:
    if path == "/auth/login" or path.startswith("/auth/google"):
        return "login", settings.rate_limit_login
    if path == "/chat":
        return "chat", settings.rate_limit_chat
    if "export" in path:
        return "export", settings.rate_limit_export
    if method in _WRITE_METHODS:
        return "write", settings.rate_limit_write
    return "global", settings.rate_limit_global


def _identity(request) -> str:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        payload = decode_access_token(header[7:].strip())
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    client = request.client
    host = client.host if client else "unknown"
    return f"ip:{host}"

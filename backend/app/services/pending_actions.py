"""Almacén en memoria de acciones de escritura propuestas por el chat.

Ninguna acción se ejecuta hasta que el usuario la confirma desde la interfaz.
Las propuestas viven un tiempo limitado y se consumen una sola vez.
"""

import secrets
import time
from typing import Any

TTL_SECONDS = 600

_store: dict[str, dict[str, Any]] = {}


def _purge() -> None:
    now = time.time()
    for token in [t for t, entry in _store.items() if entry["expires_at"] <= now]:
        _store.pop(token, None)


def create(
    *,
    user_id: str,
    thread_id: str,
    tool: str,
    args: dict[str, Any],
    summary: str,
) -> dict[str, Any]:
    _purge()
    token = secrets.token_urlsafe(16)
    _store[token] = {
        "user_id": user_id,
        "thread_id": thread_id,
        "tool": tool,
        "args": args,
        "summary": summary,
        "expires_at": time.time() + TTL_SECONDS,
    }
    return {"token": token, "tool": tool, "args": args, "summary": summary}


def pop(*, user_id: str, thread_id: str, token: str) -> dict[str, Any] | None:
    _purge()
    entry = _store.pop(token, None)
    if entry is None:
        return None
    if entry["user_id"] != user_id or entry["thread_id"] != thread_id:
        return None
    return entry


def reset() -> None:
    _store.clear()

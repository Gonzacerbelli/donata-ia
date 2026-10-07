import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.errors import register_exception_handlers
from .db import close_db, connect_db, init_indexes, ping
from .middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from .routers import auth as auth_router
from .routers import chat as chat_router
from .routers import clients as clients_router
from .routers import exports as exports_router
from .routers import notifications as notifications_router
from .routers import products as products_router
from .routers import providers as providers_router
from .routers import reports as reports_router
from .routers import sales as sales_router
from .routers import stock as stock_router
from .services.llm import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await init_indexes()
    try:
        await asyncio.to_thread(vector_store.ingest_knowledge_base)
    except Exception as exc:  # pragma: no cover - arranque tolerante a fallos de IA
        import logging

        logging.getLogger(__name__).warning("no se pudo preparar la base vectorial: %s", exc)
    yield
    await close_db()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

register_exception_handlers(app)

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(providers_router.router)
app.include_router(products_router.router)
app.include_router(clients_router.router)
app.include_router(sales_router.router)
app.include_router(stock_router.router)
app.include_router(reports_router.router)
app.include_router(exports_router.router)
app.include_router(notifications_router.router)


async def _check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
        return response.status_code == 200
    except Exception:  # pragma: no cover - health tolerante a caídas de IA
        return False


@app.get("/health")
async def health():
    mongo_ok = await ping()
    ollama_ok = await _check_ollama()
    healthy = mongo_ok and ollama_ok
    return {
        "status": "ok" if healthy else "degraded",
        "services": {"mongo": mongo_ok, "ollama": ollama_ok},
    }

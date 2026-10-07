import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.errors import register_exception_handlers
from .db import close_db, connect_db, init_indexes, ping
from .routers import auth as auth_router
from .routers import chat as chat_router
from .routers import clients as clients_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/health")
async def health():
    ok = await ping()
    return {"status": "ok" if ok else "degraded"}

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.errors import register_exception_handlers
from .db import close_db, connect_db, init_indexes, ping
from .routers import auth as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await init_indexes()
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


@app.get("/health")
async def health():
    ok = await ping()
    return {"status": "ok" if ok else "degraded"}

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.dynamodb import ensure_agents_table
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.seed import seed_bootstrap_admin

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(ensure_agents_table)
    await seed_bootstrap_admin()
    yield


app = FastAPI(title="Panasa Agent Builder", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.router import router
from core.worker import worker_loop
try:
    from generate_token import create_test_token
except ModuleNotFoundError:
    create_test_token = None

logger = logging.getLogger("core.startup")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if create_test_token is not None:
        token = create_test_token(affiliate_id=1)
        logger.warning("TEST AUTH TOKEN (core): Bearer %s", token)
    else:
        logger.info("generate_token.py not found; skipping test token logging")
    stop_event = asyncio.Event()
    task = asyncio.create_task(worker_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await task


app = FastAPI(
    title="Lead Processing System - Core API",
    summary="Lead analytics API and background deduplication worker.",
    description=(
        "Core service runs background lead consumer, deduplicates messages, persists leads in PostgreSQL "
        "and provides analytics endpoints for authenticated affiliates."
    ),
    version="1.0.0",
    contact={"name": "Lead Processing Team"},
    lifespan=lifespan,
)
app.include_router(router)

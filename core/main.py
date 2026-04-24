import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.router import router
from core.worker import worker_loop


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_event = asyncio.Event()
    task = asyncio.create_task(worker_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await task


app = FastAPI(title="Core Service", lifespan=lifespan)
app.include_router(router)

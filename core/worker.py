import asyncio
import os

from dotenv import load_dotenv
from redis.asyncio import from_url

from common.database import async_session_local
from common.models import Lead
from common.schemas import LeadQueueMessage
from core.deduplication import is_new_lead

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not set")

QUEUE_NAME = os.getenv("LEADS_QUEUE_NAME", "leads_queue")
redis = from_url(REDIS_URL, decode_responses=True)


async def process_message(raw_payload: str) -> None:
    data = LeadQueueMessage.model_validate_json(raw_payload)
    fresh = await is_new_lead(
        name=data.name,
        phone=data.phone,
        offer_id=data.offer_id,
        affiliate_id=data.affiliate_id,
    )
    if not fresh:
        return

    async with async_session_local() as session:
        lead = Lead(
            affiliate_id=data.affiliate_id,
            offer_id=data.offer_id,
            name=data.name,
            phone=data.phone,
        )
        session.add(lead)
        await session.commit()


async def worker_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            item = await redis.blpop(QUEUE_NAME, timeout=3)
            if item is None:
                continue
            _, payload = item
            await process_message(payload)
        except Exception:
            await asyncio.sleep(1)

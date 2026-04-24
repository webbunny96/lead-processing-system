import os

from dotenv import load_dotenv
from redis.asyncio import from_url

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not set")

QUEUE_NAME = os.getenv("LEADS_QUEUE_NAME", "leads_queue")
redis = from_url(REDIS_URL, decode_responses=True)


async def enqueue_lead(payload: str) -> None:
    await redis.rpush(QUEUE_NAME, payload)

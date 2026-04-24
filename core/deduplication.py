import hashlib
import os

from dotenv import load_dotenv
from redis.asyncio import from_url

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not set")

TTL_SECONDS = 600
redis = from_url(REDIS_URL, decode_responses=True)


def build_dedup_key(name: str, phone: str, offer_id: int, affiliate_id: int) -> str:
    payload = f"{name.strip().lower()}|{phone.strip()}|{offer_id}|{affiliate_id}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"lead_dedup:{digest}"


async def is_new_lead(name: str, phone: str, offer_id: int, affiliate_id: int) -> bool:
    key = build_dedup_key(name=name, phone=phone, offer_id=offer_id, affiliate_id=affiliate_id)
    # SET key value NX EX 600 -> returns True if key was created.
    created = await redis.set(key, "1", ex=TTL_SECONDS, nx=True)
    return bool(created)

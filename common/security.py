import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import Affiliate

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme")
    return parts[1]


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return payload


async def verify_token(token: str, db: AsyncSession) -> Affiliate:
    payload = decode_token(token)
    affiliate_id = payload.get("affiliate_id")
    if affiliate_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload missing affiliate_id")

    result = await db.execute(select(Affiliate).where(Affiliate.id == int(affiliate_id)))
    affiliate = result.scalar_one_or_none()
    if affiliate is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Affiliate not found")
    return affiliate


async def get_current_affiliate(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Affiliate:
    token = _extract_bearer_token(authorization)
    return await verify_token(token, db)

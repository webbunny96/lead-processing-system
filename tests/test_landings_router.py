import pytest
from fastapi import HTTPException
from types import SimpleNamespace
from unittest.mock import AsyncMock

from common.schemas import LeadCreate
from landings import router as landings_router


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_create_lead_raises_on_affiliate_mismatch():
    lead = LeadCreate(
        affiliate_id=2,
        offer_id=10,
        name="John Smith",
        phone="+123456789",
        country="UA",
    )
    affiliate = SimpleNamespace(id=1)
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await landings_router.create_lead(lead=lead, affiliate=affiliate, db=db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_lead_raises_when_offer_not_found():
    lead = LeadCreate(
        affiliate_id=1,
        offer_id=10,
        name="John Smith",
        phone="+123456789",
        country="UA",
    )
    affiliate = SimpleNamespace(id=1)
    db = AsyncMock()
    db.execute.return_value = _Result(None)

    with pytest.raises(HTTPException) as exc:
        await landings_router.create_lead(lead=lead, affiliate=affiliate, db=db)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_lead_enqueues_message(monkeypatch):
    lead = LeadCreate(
        affiliate_id=1,
        offer_id=10,
        name="John Smith",
        phone="+123456789",
        country="UA",
    )
    affiliate = SimpleNamespace(id=1)
    db = AsyncMock()
    db.execute.return_value = _Result(SimpleNamespace(id=10))
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(landings_router, "enqueue_lead", enqueue_mock)

    response = await landings_router.create_lead(lead=lead, affiliate=affiliate, db=db)

    assert response.status == "ok"
    enqueue_mock.assert_awaited_once()

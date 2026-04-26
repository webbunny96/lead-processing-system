from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from core import router as core_router


class _Result:
    def __init__(self, leads):
        self._leads = leads

    def scalars(self):
        return self

    def all(self):
        return self._leads


def _lead(lead_id, affiliate_id, offer_id, created_at):
    return SimpleNamespace(
        id=lead_id,
        affiliate_id=affiliate_id,
        offer_id=offer_id,
        name=f"Lead {lead_id}",
        phone=f"+100000{lead_id}",
        country="UA",
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_get_leads_analytics_rejects_invalid_range():
    db = AsyncMock()
    affiliate = SimpleNamespace(id=1)

    with pytest.raises(HTTPException) as exc:
        await core_router.get_leads_analytics(
            date_from=datetime(2026, 4, 3).date(),
            date_to=datetime(2026, 4, 1).date(),
            group="date",
            affiliate=affiliate,
            db=db,
        )

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_get_leads_analytics_group_by_date():
    db = AsyncMock()
    db.execute.return_value = _Result(
        [
            _lead(1, 1, 10, datetime(2026, 4, 1, 10, 0)),
            _lead(2, 1, 10, datetime(2026, 4, 1, 11, 0)),
            _lead(3, 1, 20, datetime(2026, 4, 2, 9, 0)),
        ]
    )
    affiliate = SimpleNamespace(id=1)

    response = await core_router.get_leads_analytics(
        date_from=datetime(2026, 4, 1).date(),
        date_to=datetime(2026, 4, 2).date(),
        group="date",
        affiliate=affiliate,
        db=db,
    )

    assert len(response) == 2
    assert response[0].count == 2
    assert response[1].count == 1


@pytest.mark.asyncio
async def test_get_leads_analytics_group_by_offer():
    db = AsyncMock()
    db.execute.return_value = _Result(
        [
            _lead(1, 1, 10, datetime(2026, 4, 1, 10, 0)),
            _lead(2, 1, 10, datetime(2026, 4, 1, 11, 0)),
            _lead(3, 1, 20, datetime(2026, 4, 2, 9, 0)),
        ]
    )
    affiliate = SimpleNamespace(id=1)

    response = await core_router.get_leads_analytics(
        date_from=datetime(2026, 4, 1).date(),
        date_to=datetime(2026, 4, 2).date(),
        group="offer",
        affiliate=affiliate,
        db=db,
    )

    assert len(response) == 2
    assert response[0].offer_id == 10
    assert response[0].count == 2
    assert response[1].offer_id == 20
    assert response[1].count == 1

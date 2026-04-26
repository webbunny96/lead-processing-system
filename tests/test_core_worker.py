from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from core import worker as core_worker


@pytest.mark.asyncio
async def test_process_message_skips_duplicate(monkeypatch):
    payload = (
        '{"affiliate_id":1,"offer_id":9,"name":"Alex","phone":"+12345","country":"UA"}'
    )
    dedup_mock = AsyncMock(return_value=False)
    session_factory = AsyncMock()
    monkeypatch.setattr(core_worker, "is_new_lead", dedup_mock)
    monkeypatch.setattr(core_worker, "async_session_local", session_factory)

    await core_worker.process_message(payload)

    dedup_mock.assert_awaited_once()
    session_factory.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_persists_fresh_lead(monkeypatch):
    payload = (
        '{"affiliate_id":1,"offer_id":9,"name":"Alex","phone":"+12345","country":"UA"}'
    )
    dedup_mock = AsyncMock(return_value=True)
    session = AsyncMock()
    session.add = Mock()

    @asynccontextmanager
    async def fake_session_local():
        yield session

    monkeypatch.setattr(core_worker, "is_new_lead", dedup_mock)
    monkeypatch.setattr(core_worker, "async_session_local", fake_session_local)

    await core_worker.process_message(payload)

    dedup_mock.assert_awaited_once()
    session.add.assert_called_once()
    session.commit.assert_awaited_once()

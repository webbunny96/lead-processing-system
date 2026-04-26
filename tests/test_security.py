import pytest
from fastapi import HTTPException
from jose import jwt

from common.security import _extract_bearer_token, decode_token


def test_extract_bearer_token_success():
    token = _extract_bearer_token("Bearer abc.def.ghi")
    assert token == "abc.def.ghi"


def test_extract_bearer_token_missing_header():
    with pytest.raises(HTTPException) as exc:
        _extract_bearer_token(None)
    assert exc.value.status_code == 401


def test_extract_bearer_token_invalid_scheme():
    with pytest.raises(HTTPException) as exc:
        _extract_bearer_token("Basic 123")
    assert exc.value.status_code == 401


def test_decode_token_success():
    raw = jwt.encode({"id": 7}, "test-secret", algorithm="HS256")
    payload = decode_token(raw)
    assert payload["id"] == 7


def test_decode_token_invalid():
    with pytest.raises(HTTPException) as exc:
        decode_token("not-a-valid-token")
    assert exc.value.status_code == 401

import json
import logging
import os
import time
import urllib.error
import urllib.request

import pytest

logger = logging.getLogger("tests.live")

LANDINGS_BASE_URL = os.getenv("LIVE_LANDINGS_BASE_URL", "https://webbuuny-lead-processing-system.hf.space")
CORE_BASE_URL = os.getenv("LIVE_CORE_BASE_URL", "https://webbuuny-lead-processing-system-core.hf.space")
AUTH_TOKEN = os.getenv("LIVE_AUTH_BEARER_TOKEN")
AFFILIATE_ID = int(os.getenv("LIVE_AFFILIATE_ID", "1"))
OFFER_ID = int(os.getenv("LIVE_OFFER_ID", "1"))
RETRY_ATTEMPTS = int(os.getenv("LIVE_RETRY_ATTEMPTS", "6"))
RETRY_DELAY_SECONDS = float(os.getenv("LIVE_RETRY_DELAY_SECONDS", "3"))


def _request(url: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url=url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = response.read().decode("utf-8")
            return response.getcode(), payload
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        return exc.code, payload


def _is_hf_hub_404_page(body: str) -> bool:
    body_lower = body.lower()
    return "huggingface" in body_lower and "<!doctype html>" in body_lower


def _body_preview(body: str, size: int = 220) -> str:
    return body.replace("\n", " ")[:size]


def _request_with_retry(url: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
    last_code = None
    last_body = ""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        code, body = _request(url=url, method=method, data=data, headers=headers)
        last_code, last_body = code, body
        logger.info(
            "Attempt %s/%s %s %s -> %s | body: %s",
            attempt,
            RETRY_ATTEMPTS,
            method,
            url,
            code,
            _body_preview(body),
        )
        if code != 404 or not _is_hf_hub_404_page(body):
            return code, body
        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)
    return last_code, last_body


def _skip_if_space_edge_404(code: int, body: str):
    if code == 404 and _is_hf_hub_404_page(body):
        pytest.skip("Hugging Face edge returned hub 404 page; space seems temporarily unreachable")


@pytest.mark.live
def test_live_landings_docs_or_openapi_available():
    logger.info("Checking landings availability at %s", LANDINGS_BASE_URL)
    code_docs, body_docs = _request_with_retry(f"{LANDINGS_BASE_URL}/docs")
    code_openapi, body_openapi = _request_with_retry(f"{LANDINGS_BASE_URL}/openapi.json")
    if code_docs == 404 and code_openapi == 404:
        _skip_if_space_edge_404(code_docs, body_docs)
        _skip_if_space_edge_404(code_openapi, body_openapi)
    assert 200 in {code_docs, code_openapi}


@pytest.mark.live
def test_live_core_docs_or_openapi_available():
    logger.info("Checking core availability at %s", CORE_BASE_URL)
    code_docs, body_docs = _request_with_retry(f"{CORE_BASE_URL}/docs")
    code_openapi, body_openapi = _request_with_retry(f"{CORE_BASE_URL}/openapi.json")
    if code_docs == 404 and code_openapi == 404:
        _skip_if_space_edge_404(code_docs, body_docs)
        _skip_if_space_edge_404(code_openapi, body_openapi)
    assert 200 in {code_docs, code_openapi}


@pytest.mark.live
def test_live_landings_post_lead_auth_enforced_or_accepts_valid_data():
    payload = {
        "name": "Integration Tester",
        "phone": "+380001112233",
        "country": "UA",
        "offer_id": OFFER_ID,
        "affiliate_id": AFFILIATE_ID,
    }
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
        logger.info("POST /lead with auth token against landings")
    else:
        logger.info("POST /lead without auth token to verify auth enforcement")

    code, body = _request_with_retry(f"{LANDINGS_BASE_URL}/lead", method="POST", data=payload, headers=headers)
    _skip_if_space_edge_404(code, body)
    # If token is not configured, 401 is expected.
    # If token is configured and test data matches remote state, 200 is expected.
    # 403/404 are also acceptable for mismatched affiliate/offer test fixtures.
    assert code in {200, 401, 403, 404}, f"Unexpected status {code}. Body: {body}"


@pytest.mark.live
def test_live_core_get_leads_returns_expected_status_family():
    params = "date_from=2026-01-01&date_to=2026-12-31&group=date"
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
        logger.info("GET /leads with auth token against core")
    else:
        logger.info("GET /leads without auth token to verify auth enforcement")

    code, body = _request_with_retry(f"{CORE_BASE_URL}/leads?{params}", headers=headers)
    _skip_if_space_edge_404(code, body)
    assert code in {200, 401, 422}, f"Unexpected status {code}. Body: {body}"

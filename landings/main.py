import logging

from fastapi import FastAPI

from landings.router import router
try:
    from generate_token import create_test_token
except ModuleNotFoundError:
    create_test_token = None

logger = logging.getLogger("landings.startup")

app = FastAPI(
    title="Lead Processing System - Landings API",
    summary="Lead intake API with JWT authorization and queue publishing.",
    description=(
        "Landings service accepts incoming leads from partners, validates JWT bearer token "
        "and business rules, and pushes valid leads to Redis queue for core processing."
    ),
    version="1.0.0",
    contact={"name": "Lead Processing Team"},
)
app.include_router(router)


@app.on_event("startup")
async def log_test_token() -> None:
    if create_test_token is not None:
        token = create_test_token(affiliate_id=1)
        logger.warning("TEST AUTH TOKEN (landings): Bearer %s", token)
    else:
        logger.info("generate_token.py not found; skipping test token logging")

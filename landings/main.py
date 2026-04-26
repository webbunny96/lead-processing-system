import logging

from fastapi import FastAPI

from landings.router import router
try:
    from generate_token import create_test_token
except ModuleNotFoundError:
    create_test_token = None

logger = logging.getLogger("landings.startup")

app = FastAPI(title="Landings Service")
app.include_router(router)


@app.on_event("startup")
async def log_test_token() -> None:
    if create_test_token is not None:
        token = create_test_token(affiliate_id=1)
        logger.warning("TEST AUTH TOKEN (landings): Bearer %s", token)
    else:
        logger.info("generate_token.py not found; skipping test token logging")

import logging
import os

import pytest

# Provide safe defaults so module-level env checks do not fail in tests.
# Asyncpg is already in project dependencies; no real DB connection is opened in unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("LEADS_QUEUE_NAME", "test_leads_queue")

logger = logging.getLogger("tests")


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="run tests that call deployed external services",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return
    skip_live = pytest.mark.skip(reason="need --run-live option to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def log_test_boundaries(request):
    logger.info("START %s", request.node.nodeid)
    yield
    logger.info("END   %s", request.node.nodeid)

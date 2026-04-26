import os


# Provide safe defaults so module-level env checks do not fail in tests.
# Asyncpg is already in project dependencies; no real DB connection is opened in unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("LEADS_QUEUE_NAME", "test_leads_queue")

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Створюємо асинхронний двигун (Engine)
# За ТЗ використовуємо asyncpg
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    # Supabase transaction pooler (PgBouncer) requires disabled statement cache.
    connect_args={"statement_cache_size": 0},
)

# Фабрика сесій для роботи з базою
async_session_local = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Базовий клас для моделей (SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass

# Dependency для FastAPI
async def get_db():
    async with async_session_local() as session:
        yield session
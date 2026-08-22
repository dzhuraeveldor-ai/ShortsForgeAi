from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from worker.config import settings

Base = declarative_base()


def _get_async_database_url():
    url = settings.DATABASE_URL
    if url.startswith("sqlite://"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url


# Async engine
async_engine = create_engine(
    _get_async_database_url(),
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_="AsyncSession",
    expire_on_commit=False
)

# Sync engine for job processor threads
sync_engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False
)


async def get_db_session():
    """Async database session generator for FastAPI dependencies."""
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSessionLocal() as session:
        yield session


def get_db_session_sync():
    """Get a synchronous database session for use in threads."""
    return SyncSessionLocal()


def init_database():
    """Initialize database tables (sync)."""
    Base.metadata.create_all(bind=sync_engine)

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app

TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


# @pytest_asyncio.fixture
# async def client() -> AsyncClient:
#     app.dependency_overrides[get_db] = override_get_db
#     async with AsyncClient(
#         transport=ASGITransport(app=app), base_url="http://test"
#     ) as ac:
#         yield ac
#     app.dependency_overrides.clear()


class FakeRedis:
    def __init__(self):
        self._store = {}

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    fake_redis = FakeRedis()

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.security import create_access_token, hash_password
from app.core.base import Base
from app.core.config import settings
from app.core.database import get_db
from app.core.enums import UserRole
from app.core.redis import get_redis
from app.main import app
from app.user.models import User

TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


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


async def create_test_user(db: AsyncSession, role: UserRole, email: str) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        hashed_password=hash_password("testpass123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def cleanup_database():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

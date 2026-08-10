from collections.abc import AsyncGenerator

import app.core.dynamodb as dynamodb_module
import pytest
from app.core.database import Base, get_async_session
from app.core.dynamodb import ensure_agents_table
from app.core.users import UserManager
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx import ASGITransport, AsyncClient
from moto import mock_aws
from shared.auth.roles import Role
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient]:
    async def _get_async_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = _get_async_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(session_factory):
    async def _make_user(
        email: str, password: str, role: Role = Role.ANALYST, tenant_id: str = "tenant-a"
    ) -> User:
        async with session_factory() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)
            return await user_manager.create(
                UserCreate(email=email, password=password, role=role, tenant_id=tenant_id)
            )

    return _make_user


@pytest.fixture
def dynamodb_table(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        dynamodb_module._resource = None
        ensure_agents_table()
        yield
        dynamodb_module._resource = None

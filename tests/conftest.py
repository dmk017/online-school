# conftest.py
from typing import AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import ASGITransport, AsyncClient
import settings
from main import app
import os
import asyncio
from db.session import get_db
import asyncpg
import sys


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- Миграции (синхронно, сессия) ---
@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    if not os.path.exists("migrations"):
        os.system("alembic init migrations")

    # при разработке можно закомментировать создание новой ревизии, если оно лишнее
    os.system('alembic revision --autogenerate -m "test runnnig migrations"')
    os.system("alembic upgrade heads")


# --- asyncpg_pool: создаём на каждый тест, чтобы он использовал тот же loop ---
@pytest.fixture(scope="function")
async def asyncpg_pool():
    dsn = "".join(settings.TEST_DATABASE_URL.split("+asyncpg"))
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
    try:
        yield pool
    finally:
        await pool.close()


CLEAN_TABLES = [
    "users",
]


# --- ВАЖНО: фабрика движка/сессий теперь создаётся в фикстуре function-scoped ---
@pytest.fixture(scope="function")
async def async_session_test():
    # создаём движок и фабрику сессий внутри текущего loop
    engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        yield async_session
    finally:
        # корректное освобождение ресурсов движка
        await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(asyncpg_pool):
    """Перед каждым тестом очищаем таблицы"""
    async with asyncpg_pool.acquire() as conn:
        for table in CLEAN_TABLES:
            await conn.execute(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;')


@pytest.fixture(scope="function")
async def client(async_session_test) -> AsyncGenerator[AsyncClient, None]:
    # override зависимости, чтобы FastAPI использовал нашу тестовую фабрику сессий
    async def _get_test_db():
        yield async_session_test()

    app.dependency_overrides[get_db] = _get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def get_user_from_database(asyncpg_pool):

    async def get_user_from_database_by_uuid(user_id: str):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)

    return get_user_from_database_by_uuid


@pytest.fixture
async def create_user_in_database(asyncpg_pool):

    async def create_user_in_database(user_id: str, name: str, surname: str, email: str, is_active: bool):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetchrow(
                "INSERT INTO users(user_id, name, surname, email, is_active) VALUES ($1, $2, $3, $4, $5) RETURNING *",
                user_id, name, surname, email, is_active
            )

    return create_user_in_database

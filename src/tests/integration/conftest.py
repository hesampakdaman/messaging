import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import pathlib
import uuid

import asyncpg
from fastapi import FastAPI
import httpx
import pytest
import pytest_asyncio
import uvicorn

from messaging.adapters import repository
from messaging.adapters.http.handlers import app as http_app
from messaging.service.service import Service

from .app_fixture import AppFixture

MIGRATIONS_DIR = pathlib.Path(repository.__file__).parent / "migrations"
pytestmark = pytest.mark.asyncio


async def _apply_migrations(dsn: str, schema: str) -> None:
    conn = await asyncpg.connect(dsn=dsn)
    try:
        _ = await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            async with conn.transaction():
                _ = await conn.execute(f'SET LOCAL search_path TO "{schema}"')
                _ = await conn.execute(sql)
    finally:
        await conn.close()


def _pick_free_port() -> int:
    import socket as _s

    with _s.socket(_s.AF_INET, _s.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest_asyncio.fixture
async def app(pg_dsn: str) -> AsyncIterator[AppFixture]:
    schema = f"t_{uuid.uuid4().hex[:8]}"
    await _apply_migrations(pg_dsn, schema)

    pool: asyncpg.Pool = await asyncpg.create_pool(
        dsn=pg_dsn,
        server_settings={"search_path": schema},
        min_size=1,
        max_size=1,
    )
    logger = logging.getLogger("messaging.test")
    service = Service(repository.PostgresManager(pool), logger)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service
        yield

    http_app.router.lifespan_context = lifespan

    port = _pick_free_port()
    server = uvicorn.Server(uvicorn.Config(http_app, host="127.0.0.1", port=port, log_level="warning"))
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.01)

    client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=10.0)
    try:
        yield AppFixture(service, pool, client)
    finally:
        server.should_exit = True
        await task
        await client.aclose()
        await pool.close()

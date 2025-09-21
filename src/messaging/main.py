from contextlib import asynccontextmanager
import logging
import os

import asyncpg
from fastapi import FastAPI

from messaging import adapters
from messaging.adapters import repository
from messaging.service import Service


async def create_postgres() -> repository.PostgresManager:
    dsn = os.getenv("DATABASE_URL", "postgresql://messaging:messaging@localhost:5432/messaging")
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
    return repository.PostgresManager(pool)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger("messaging")
    logger.setLevel(logging.INFO)
    logger.info("service starting")
    pg = await create_postgres()
    app.state.service = Service(pg, logger)
    try:
        logger.info("service ready")
        yield
    finally:
        await pg.close()


logging.basicConfig(level=logging.INFO)
app: FastAPI = adapters.http.app
app.router.lifespan_context = lifespan

# pyright: reportAttributeAccessIssue = false
import os

import pytest
from testcontainers.core.container import LogMessageWaitStrategy
from testcontainers.postgres import PostgresContainer


def _is_worker() -> bool:
    return os.environ.get("PYTEST_XDIST_WORKER") is not None


def _start_pg():
    pg = PostgresContainer("postgres:17-alpine")
    _ = pg.waiting_for(LogMessageWaitStrategy("database system is ready to accept connections")).start()
    dsn = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
    return pg, dsn


def pytest_configure(config: pytest.Config) -> None:
    # starts the container exactly once in the top-most pytest controller
    if _is_worker():
        return
    pg, dsn = _start_pg()
    config._pg_container = pg
    config._pg_dsn = dsn


def pytest_unconfigure(config: pytest.Config) -> None:
    # stops the container once in the top-most pytest controller
    if _is_worker():
        return
    pg = getattr(config, "_pg_container", None)
    assert pg is not None
    _ = pg.stop()


def pytest_configure_node(node) -> None:
    # injects the dsn from the top-most pytest controller to xdist
    # workers
    dsn = getattr(node.config, "_pg_dsn", None)
    node.workerinput["pg_dsn"] = dsn


@pytest.fixture(scope="session")
def pg_dsn(request: pytest.FixtureRequest) -> str:
    if _is_worker():
        wi = getattr(request.config, "workerinput", {}) or {}
        dsn = wi.get("pg_dsn")
    else:
        dsn = getattr(request.config, "_pg_dsn", None)
    if not dsn:
        raise RuntimeError("pg_dsn not provided")
    return dsn

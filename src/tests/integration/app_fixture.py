import asyncpg
import httpx

from messaging.service.service import Service

from . import helpers


class AppFixture:
    def __init__(self, service: Service, pool: asyncpg.Pool, client: httpx.AsyncClient):
        self.service: Service = service
        self.pool: asyncpg.Pool = pool
        self.http: helpers.HttpClient = helpers.HttpClient(client)

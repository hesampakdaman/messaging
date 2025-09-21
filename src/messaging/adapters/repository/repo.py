from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
import json
from typing import cast

import asyncpg

from messaging.domain import models


class Postgres:
    def __init__(self, conn: asyncpg.pool.PoolConnectionProxy):
        self._conn: asyncpg.pool.PoolConnectionProxy = conn

    async def add(self, msg: models.Message) -> models.MessageID:
        query = """
        WITH next AS (
          INSERT INTO channel_sequences (channel, last_seq)
          VALUES ($2, 0)
          ON CONFLICT (channel)
          DO UPDATE SET last_seq = channel_sequences.last_seq + 1
          RETURNING last_seq
        )
        INSERT INTO messages (id, seq, channel, payload, published_at)
        SELECT $1::uuid, next.last_seq, $2::text, $3::jsonb, $4::timestamptz
        FROM next
        RETURNING id
        """
        return cast(
            models.MessageID,
            await self._conn.fetchval(
                query,
                msg.id,
                msg.channel,
                json.dumps(msg.payload),
                msg.published_at,
            ),
        )

    async def list_unread(self, channel: models.Channel, consumer: models.Consumer) -> list[models.Message]:
        query = """
        SELECT m.id, m.channel, m.payload, m.published_at
        FROM messages m
        LEFT JOIN message_reads r
          ON m.id = r.message_id AND r.consumer = $2
        WHERE r.message_id IS NULL
          AND m.channel = $1
        ORDER BY m.seq ASC
        """
        rows: list[asyncpg.Record] = await self._conn.fetch(query, channel, consumer)
        return list(map(_to_message, rows))

    async def list_from_sequence(self, channel: models.Channel, from_sequence: int) -> list[models.Message]:
        query = """
        SELECT m.id, m.channel, m.payload, m.published_at
        FROM messages m
        WHERE m.channel = $1
          AND m.seq >= $2
        ORDER BY m.seq ASC
        """
        rows: list[asyncpg.Record] = await self._conn.fetch(query, channel, from_sequence)
        return list(map(_to_message, rows))

    async def mark_read(
        self,
        message_id: models.MessageID,
        consumer: models.Consumer,
        read_at: datetime,
    ) -> None:
        query = """
        INSERT INTO message_reads (message_id, consumer, read_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (message_id, consumer)
        DO UPDATE SET read_at = EXCLUDED.read_at
        """
        _ = await self._conn.execute(query, message_id, consumer, read_at)


class PostgresManager:
    def __init__(self, pool: asyncpg.Pool):
        self._pool: asyncpg.Pool = pool

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[Postgres]:
        async with self._pool.acquire() as conn, conn.transaction():
            yield Postgres(conn)

    async def close(self) -> None:
        await self._pool.close()


def _to_message(r: asyncpg.Record) -> models.Message:
    return models.Message(
        id=cast(models.MessageID, r["id"]),
        channel=cast(models.Channel, r["channel"]),
        payload=cast(models.JSON, json.loads(r["payload"])),  # pyright: ignore[reportAny]
        published_at=cast(datetime, r["published_at"]),
    )

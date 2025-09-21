from typing import Literal

import httpx
from httpx import URL

from messaging.adapters.http import schema
from messaging.domain import models

Method = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class HttpClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client: httpx.AsyncClient = client

    async def request(
        self,
        method: Method,
        path: URL,
        *,
        json: models.JSON | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._client.request(method, path, json=json, headers=headers)

    async def publish(self, ch: models.Channel, payload: models.JSON) -> models.MessageID:
        resp = await self.request(
            "POST",
            URL(f"/channels/{ch}/publish"),
            json=schema.PublishRequest(payload=payload).model_dump(),
        )
        return schema.PublishResponse.model_validate_json(resp.text).id

    async def list_unread(self, ch: models.Channel, con: models.Consumer) -> list[models.Message]:
        resp = await self.request(
            "GET",
            URL(f"/channels/{ch}/messages/unread"),
            headers={"X-Consumer": con},
        )
        return schema.GetMessagesResponse.model_validate_json(resp.text).messages

    async def list_from_sequence(self, ch: models.Channel, from_sequence: int) -> list[models.Message]:
        resp = await self.request(
            "GET",
            URL(f"/channels/{ch}/messages/from/{from_sequence}"),
        )
        return schema.GetMessagesResponse.model_validate_json(resp.text).messages

    async def ack(self, id: models.MessageID, con: models.Consumer) -> None:
        resp = await self.request(
            "POST",
            URL(f"/messages/{id}/ack"),
            headers={"X-Consumer": con},
        )
        assert resp.status_code in (200, 204), resp.text


def expect_message_equal_ignoring_time(*, actual: models.Message, expected: models.Message) -> None:
    aligned_expected = models.Message(
        id=expected.id,
        channel=expected.channel,
        payload=expected.payload,
        published_at=actual.published_at,
    )
    assert actual == aligned_expected

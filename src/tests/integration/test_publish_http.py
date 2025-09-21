from uuid import UUID

from httpx import URL
import pytest

from messaging.adapters.http import schema
from messaging.domain import models

from .app_fixture import AppFixture

pytestmark = pytest.mark.asyncio


async def test_publish__201_returns_valid_id(app: AppFixture):
    # Given
    channel = models.Channel("orders")
    body = schema.PublishRequest(payload={"hello": "world"}).model_dump()

    # When
    resp = await app.http.request("POST", URL(f"/channels/{channel}/publish"), json=body)

    # Then
    assert resp.status_code == 201, resp.text
    published = schema.PublishResponse.model_validate_json(resp.text)
    _ = UUID(str(published.id))


async def test_publish__422_when_payload_is_not_json(app: AppFixture):
    # Given
    channel = models.Channel("orders")

    # When
    resp = await app.http.request(
        "POST",
        URL(f"/channels/{channel}/publish"),
        json={"payload": "not-a-dict"},  # violates PublishRequest
    )

    # Then
    assert resp.status_code == 422, resp.text

import uuid

from httpx import URL
import pytest

from messaging.domain import models

from .app_fixture import AppFixture

pytestmark = pytest.mark.asyncio


async def test_list_from_sequence__422_when_seq_is_zero(app: AppFixture):
    # Given
    channel = models.Channel("orders")

    # When: call path with from_seq = 0 (violates ge=1)
    resp = await app.http.request("GET", URL(f"/channels/{channel}/messages/from/0"))

    # Then
    assert resp.status_code == 422, resp.text


async def test_list_from_sequence__channel_isolation(app: AppFixture):
    # Given: messages in two channels
    ch_a = models.Channel(f"orders-a-{uuid.uuid4()}")
    ch_b = models.Channel(f"orders-b-{uuid.uuid4()}")

    ids_a = [await app.http.publish(ch_a, {"c": "a", "i": i}) for i in range(2)]
    _ids_b = [await app.http.publish(ch_b, {"c": "b", "i": i}) for i in range(2)]

    # When: list from seq=1 on channel A
    msgs_a = await app.http.list_from_sequence(ch_a, 1)

    # Then: only A’s ids in publish order
    assert [m.id for m in msgs_a] == ids_a
    for m in msgs_a:
        assert m.channel == ch_a

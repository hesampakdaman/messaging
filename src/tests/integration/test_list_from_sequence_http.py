from datetime import datetime
import uuid

from httpx import URL
import pytest

from messaging.domain import models

from . import helpers
from .app_fixture import AppFixture

pytestmark = pytest.mark.asyncio


async def test_list_from_sequence__200_from_zero_returns_all_in_order(app: AppFixture):
    # Given
    channel = models.Channel(f"orders-{uuid.uuid4()}")
    payloads: list[models.JSON] = [
        {"i": 1},
        {"i": 2},
        {"i": 3},
    ]

    # When: publish 3 messages
    ids = [await app.http.publish(channel, p) for p in payloads]

    # And: list from index = 1
    messages = await app.http.list_from_sequence(channel, 1)

    # Then: exactly our 3 messages in publish order
    assert [m.id for m in messages] == ids
    for m, expected_id, expected_payload in zip(messages, ids, payloads, strict=False):
        helpers.expect_message_equal_ignoring_time(
            actual=m,
            expected=models.Message(
                id=expected_id,
                channel=channel,
                payload=expected_payload,
                published_at=datetime.min,  # ignored
            ),
        )


async def test_list_from_sequence__ignores_ack_state(app: AppFixture):
    # Given
    channel = models.Channel(f"orders-{uuid.uuid4()}")
    consumer = models.Consumer("someone")
    payload: models.JSON = {"k": "v"}
    message_id = await app.http.publish(channel, payload)

    # When: ack by a consumer (should not affect list_from_sequence)
    await app.http.ack(message_id, consumer)

    # Then: list_from_sequence(1) still returns the message
    messages = await app.http.list_from_sequence(channel, 1)
    assert [m.id for m in messages] == [message_id]
    helpers.expect_message_equal_ignoring_time(
        actual=messages[0],
        expected=models.Message(
            id=message_id,
            channel=channel,
            payload=payload,
            published_at=datetime.min,
        ),
    )


async def test_list_from_sequence__reads_from_middle(app: AppFixture):
    # Given a fresh channel and 5 messages
    channel = models.Channel(f"orders-{uuid.uuid4()}")
    payloads: list[models.JSON] = [{"i": i} for i in range(5)]
    ids = [await app.http.publish(channel, p) for p in payloads]

    # When: list starting from seq >= 2 (1-based)
    messages = await app.http.list_from_sequence(channel, 2)

    # Then: we get messages starting from the second publish onward (4 items)
    assert [m.id for m in messages] == ids[1:]
    for m, expected_id, expected_payload in zip(messages, ids[1:], payloads[1:], strict=False):
        helpers.expect_message_equal_ignoring_time(
            actual=m,
            expected=models.Message(
                id=expected_id,
                channel=channel,
                payload=expected_payload,
                published_at=datetime.min,  # ignored by helper
            ),
        )


async def test_list_from_sequence__422_when_seq_is_zero(app: AppFixture):
    # Given
    channel = models.Channel("orders")

    # When: call path with from_seq = 0 (violates ge=1)
    resp = await app.http.request("GET", URL(f"/channels/{channel}/messages/from/0"))

    # Then
    assert resp.status_code == 422, resp.text


async def test_list_from_sequence__channel_isolation(app: AppFixture):
    # Given: messages in two channels
    ch_a = models.Channel("orders-a")
    ch_b = models.Channel("orders-b")

    ids_a = [await app.http.publish(ch_a, {"c": "a", "i": i}) for i in range(2)]
    _ids_b = [await app.http.publish(ch_b, {"c": "b", "i": i}) for i in range(2)]

    # When: list from seq=1 on channel A
    msgs_a = await app.http.list_from_sequence(ch_a, 1)

    # Then: only A’s ids in publish order
    assert [m.id for m in msgs_a] == ids_a
    for m in msgs_a:
        assert m.channel == ch_a

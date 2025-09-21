from datetime import datetime

from httpx import URL
import pytest

from messaging.domain import models

from . import helpers
from .app_fixture import AppFixture

pytestmark = pytest.mark.asyncio


async def test_list_unread__200_contains_published_for_consumer(app: AppFixture):
    # Given
    channel = models.Channel("orders")
    consumer = models.Consumer("tester")
    payload: models.JSON = {"hello": "world"}

    # When
    message_id = await app.http.publish(channel, payload)
    messages = await app.http.list_unread(channel, consumer)

    # Then
    msg = next((m for m in messages if m.id == message_id), None)
    assert msg is not None
    helpers.expect_message_equal_ignoring_time(
        actual=msg,
        expected=models.Message(
            id=message_id,
            channel=channel,
            payload=payload,
            published_at=datetime.min,  # ignored by helper
        ),
    )


async def test_list_unread__ack_removes_message_from_unread_for_that_consumer_only(app: AppFixture):
    # Given
    channel = models.Channel("orders")
    consumer_a = models.Consumer("alpha")
    consumer_b = models.Consumer("beta")
    payload: models.JSON = {"k": "v"}

    # When
    message_id = await app.http.publish(channel, payload)

    ## Both see it unread initially
    unread_a = await app.http.list_unread(channel, consumer_a)
    unread_b = await app.http.list_unread(channel, consumer_b)
    assert any(m.id == message_id for m in unread_a)
    assert any(m.id == message_id for m in unread_b)

    ## Ack as A
    await app.http.ack(message_id, consumer_a)

    # Then
    ## A no longer sees it, B still does
    unread_a_after = await app.http.list_unread(channel, consumer_a)
    unread_b_after = await app.http.list_unread(channel, consumer_b)
    assert all(m.id != message_id for m in unread_a_after)
    assert any(m.id == message_id for m in unread_b_after)


async def test_unread__400_without_consumer_header(app: AppFixture):
    # Given
    channel = models.Channel("orders")

    # When
    resp = await app.http.request(
        "GET",
        URL(f"/channels/{channel}/messages/unread"),
        # no X-Consumer header on purpose
    )

    # Then
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "X-Consumer header is required"

# example.py
import asyncio
import json
import os
import sys
from typing import Any
import uuid

import httpx


def pretty(x: Any) -> str:
    return json.dumps(x, indent=2, ensure_ascii=False, sort_keys=True)


API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


async def publish(client: httpx.AsyncClient, channel: str, payload: dict) -> dict:
    url = f"{API_BASE}/channels/{channel}/publish"
    r = await client.post(url, json={"payload": payload}, timeout=10.0)
    r.raise_for_status()
    return r.json()  # {"id": "<uuid>"}


async def get_unread(client: httpx.AsyncClient, channel: str, consumer: str) -> dict:
    url = f"{API_BASE}/channels/{channel}/messages/unread"
    r = await client.get(url, headers={"X-Consumer": consumer}, timeout=10.0)
    r.raise_for_status()
    return r.json()  # {"messages": [...]}


async def get_from_index(client: httpx.AsyncClient, channel: str, from_index: int) -> dict:
    url = f"{API_BASE}/channels/{channel}/messages/from/{from_index}"
    r = await client.get(url, timeout=10.0)
    r.raise_for_status()
    return r.json()  # {"messages": [...]}


async def ack(client: httpx.AsyncClient, message_id: str, consumer: str) -> None:
    url = f"{API_BASE}/messages/{message_id}/ack"
    r = await client.post(url, headers={"X-Consumer": consumer}, timeout=10.0)
    r.raise_for_status()
    # 204 No Content → nothing returned


async def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else "demo"
    consumer = sys.argv[2] if len(sys.argv) > 2 else "reporting-service"

    async with httpx.AsyncClient() as client:
        print(f"\n--- Publishing to channel='{channel}' ---")
        pub_tasks = [
            publish(client, channel, {"event": "order_created", "order_id": 1001, "nonce": str(uuid.uuid4())}),
            publish(client, channel, {"event": "order_picked", "order_id": 1001, "nonce": str(uuid.uuid4())}),
            publish(client, channel, {"event": "order_shipped", "order_id": 1001, "nonce": str(uuid.uuid4())}),
        ]
        published = await asyncio.gather(*pub_tasks)
        print(pretty(published))

        print(f"\n--- Fetch unread for consumer='{consumer}' ---")
        unread = await get_unread(client, channel, consumer)
        print(pretty(unread))

        if unread["messages"]:
            first_msg = unread["messages"][0]
            print(f"\n--- Ack first unread message {first_msg['id']} ---")
            await ack(client, first_msg["id"], consumer)
            print("Acked successfully.")

        print("\n--- Fetch from index 1 ---")
        from_idx = await get_from_index(client, channel, 1)
        print(pretty(from_idx))


if __name__ == "__main__":
    """
    Usage:
      python example.py [channel] [consumer]

    Defaults:
      channel = "demo"
      consumer = "reporting-service"

    API_BASE_URL can override host/port:
      API_BASE_URL="http://127.0.0.1:8001" python example.py
    """
    asyncio.run(main())

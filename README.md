# Messaging Service

A messaging API which exposes the following functionality:
- **Publish messages** on named channels.
- **Consume messages** with unread tracking: the service remembers which messages each consumer has read.
- **List messages** from an absolute index for stateless reads (no consumer tracking).

## Architecture
- **domain/**
  - Core types and logic: value objects like `Channel`, `Consumer`, and the `Message` entity.
- **service/**
  - The orchestration layer that coordinates repositories to execute domain commands.
- **adapters/**
  - **http/**: FastAPI handlers exposing the domain/use-cases as HTTP endpoints.
  - **repository/**: Postgres implementation (asyncpg) + migrations.

## Usage

### Start the stack

```bash
make up
# API: http://localhost:8000
```

> First run will start a Postgres container, run migrations, then boot the API.

### Publish a message
Here we create a message and publish it under the _orders_ channel.
```bash
curl -sS -X POST \
  http://localhost:8000/channels/orders/publish \
  -H 'Content-Type: application/json' \
  -d '{"payload": {"event":"order_picked","order_id":1001}}'
```

**Example response**
```json
{"id":"080dd1a0-b044-4f8b-8aad-4d7c66dd68d0"}
```

### List unread (per consumer)
Unread requires a consumer header so the system can track what each consumer has seen.
```bash
curl -sS \
  'http://localhost:8000/channels/orders/messages/unread' \
  -H 'X-Consumer: reporting-service'
```

**Example response**
```json
{
  "messages": [
    {
      "id": "080dd1a0-b044-4f8b-8aad-4d7c66dd68d0",
      "channel": "orders",
      "payload": {
        "event": "order_picked",
        "order_id": 1001
      },
      "published_at": "2025-09-21T18:25:44.253768Z"
    }
  ]
}
```

### List from a specific index (no consumer state)

```bash
curl -sS \
  'http://localhost:8000/channels/orders/messages/from/1'
```

**Example response**
```json
{
  "messages": [
    {
      "id": "080dd1a0-b044-4f8b-8aad-4d7c66dd68d0",
      "channel": "orders",
      "payload": {
        "event": "order_picked",
        "order_id": 1001
      },
      "published_at": "2025-09-21T18:25:44.253768Z"
    }
  ]
}
```

## Development

### One-time setup
```bash
make install
```

### Run automated tests
Tests run fully isolated using **pytest** with **testcontainers**. No running environment is needed; a disposable Postgres container is started automatically.
```bash
make test
```

### Lint & format
```bash
make lint
```

## Interactive testing
Start a local dev environment:
```bash
make up
```
This will start a Postgres instance, run the migrations, and start the HTTP server (Uvicorn) with reload. Then you can use cURL or your favorite HTTP client to hit the endpoints.

```bash
curl -sS -X POST \
  http://localhost:8000/channels/orders/publish \
  -H 'Content-Type: application/json' \
  -d '{"payload": {"event":"order_picked","order_id":1001}}'
```

To inspect the database go to the container:
```bash
docker exec -it messaging_db psql -U messaging
```

Tear down using:
```bash
make down
```

and if you want to tear down and also delete the volume
```bash
make fresh
```

## Helpful targets
```bash
make up        # docker compose up
make down      # docker compose down
make fresh     # docker compose down -v (delete volume)
make run       # run API normally
make test      # pytest -n auto (isolated, with testcontainers)
make fmt       # ruff format
make lint      # ruff format + ruff check --fix
make clean     # remove caches/artifacts
make lock      # uv lock
```

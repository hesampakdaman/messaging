.PHONY: install run dev test lint fmt fmt-check clean lock up down docker-build docker-run docker-shell

install:
	uv sync --dev

lock:
	uv lock

run:
	uv run uvicorn messaging.main:app --host 0.0.0.0 --port 8000 --log-level=info

test:
	uv run pytest -n auto

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format . --check

clean:
	rm -rf .pytest_cache .ruff_cache dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete

up:
	docker compose up

down:
	docker compose down

docker-build:
	docker build -t messaging:local .

docker-run:
	docker run --rm -p 8000:8000 --name messaging messaging:local

docker-shell:
	docker run --rm -it --entrypoint /bin/bash messaging:local

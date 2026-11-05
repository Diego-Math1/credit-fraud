.PHONY: setup up down dbt api test lint

setup:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt

up:
	docker compose up -d

down:
	docker compose down

dbt:
	docker compose --profile tasks run --rm dbt

api:
	uvicorn src.serving.main:app --reload --port 8000

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	black --check src/ tests/

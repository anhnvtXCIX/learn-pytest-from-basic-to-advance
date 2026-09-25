.PHONY: install test test-unit test-integration test-docker cov ex sol lint format typecheck check migrate compose-up compose-down clean

# M=06 selects a module by its two-digit prefix, e.g. `make ex M=06`.
M ?=

install:
	uv sync
	uv run alembic upgrade head

# Default suite: no Docker, no exercises. This is what CI and a fresh clone run.
test:
	uv run pytest

test-unit:
	uv run pytest -m unit

# "integration, but not the ones that need Docker" -- the fast SQLite tier.
test-integration:
	uv run pytest -m "integration and not docker"

# The Testcontainers tier. Needs a running Docker daemon. "not exercise" for the
# same reason `test` excludes it by default -- module 10's exercises are also
# docker-marked, and this target should be a clean pass on a fresh clone, same as
# `test`. Use `make ex M=10` (which needs Docker running) for those specifically.
test-docker:
	uv run pytest -m "docker and not exercise"

cov:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# Run one module's exercises (currently-failing TODO tests), verbosely.
ex:
	@if [ -z "$(M)" ]; then echo "usage: make ex M=06"; exit 1; fi
	@dir=$$(ls -d modules/$(M)-* 2>/dev/null | head -1); \
	if [ -z "$$dir" ]; then echo "no module matching modules/$(M)-*"; exit 1; fi; \
	uv run pytest "$$dir/exercises" -m exercise -v

# Run one module's reference solutions -- diff these against your own exercise
# attempt, don't just read them first.
sol:
	@if [ -z "$(M)" ]; then echo "usage: make sol M=06"; exit 1; fi
	@dir=$$(ls -d modules/$(M)-* 2>/dev/null | head -1); \
	if [ -z "$$dir" ]; then echo "no module matching modules/$(M)-*"; exit 1; fi; \
	uv run pytest "$$dir/solutions" -m exercise -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test

migrate:
	uv run alembic upgrade head

# A long-lived Postgres + Redis for poking at manually (psql, redis-cli). The test
# suite itself uses Testcontainers, not this -- see modules/10-testcontainers/README.md
# for why those are different tools for different jobs.
compose-up:
	docker compose up -d

compose-down:
	docker compose down -v

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +

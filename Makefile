.PHONY: install test lint format

install:
	uv pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=foundrai --cov-report=html
	open htmlcov/index.html

lint:
	ruff check foundrai tests
	mypy foundrai

format:
	ruff format foundrai tests

run:
	foundrai sprint-start "Build a hello world REST API"

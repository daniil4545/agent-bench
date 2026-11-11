.PHONY: lint test

lint:
	uvx ruff@0.17.2 check .
	uvx ruff@0.17.2 format --check .

test:
	uv run --no-project --with pytest==8.4.2 python -m pytest -q -p no:cacheprovider tests

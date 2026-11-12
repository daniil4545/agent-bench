.PHONY: lint test

RUFF := uvx ruff@0.17.2
GOLANGCI := go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.15.0
# Task directories with their own go.mod (the Go tasks base and solution).
GO_MODULES := $(patsubst %/go.mod,%,$(wildcard tasks/*/*/go.mod))

# All static checks; the user, the agent and CI run the same `make lint`.
lint:
	$(RUFF) format --check .
	$(RUFF) check .
	@out=$$(gofmt -l tasks); test -z "$$out" || { echo "gofmt:"; echo "$$out"; exit 1; }
	@for d in $(GO_MODULES); do echo "golangci-lint $$d"; \
	  (cd $$d && $(GOLANGCI) run -c $(CURDIR)/.golangci.yml) || exit 1; done

test:
	uv run --no-project --with pytest==8.4.2 python -m pytest -q -p no:cacheprovider tests

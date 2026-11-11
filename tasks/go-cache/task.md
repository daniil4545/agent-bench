Bug report: the `cache` package misbehaves.

Reports from users of `cache.Cache`:

1. Using one cache from several goroutines makes `go test -race` fail and sometimes crashes the
   process.
2. Entries seem to live one tick longer than their time-to-live.

The behaviour of every method is documented in the comments of `cache.go` and `stats.go`. Those
comments are the contract: make the code do what they say, including the cases the report does not
mention. Add regression tests; `go test -race ./...` must pass.

Scope: change only `cache.go`, `stats.go` and `cache_test.go`. `clock.go` is shared with other
packages and must not change.

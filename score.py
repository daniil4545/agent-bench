"""Pure scoring helpers: scope check, limit detection, usage parsing, result rows."""

import fnmatch
import json
import re
from collections.abc import Iterator

LIMIT_RE = re.compile(
    r"usage limit|rate limit|limit reached|quota|too many requests|\b429\b", re.IGNORECASE
)


def in_scope(changed: list[str], allowed: list[str]) -> bool:
    """True when every changed path matches one of the allowed names or globs."""
    return all(any(fnmatch.fnmatch(path, pat) for pat in allowed) for path in changed)


def hit_limit(output: str, exit_code: int) -> bool:
    """A failed run whose output talks about a subscription or rate limit."""
    return exit_code != 0 and bool(LIMIT_RE.search(output))


AUTH_RE = re.compile(
    r"failed to authenticate|not logged in|please (log ?in|run /login)|unauthorized|\b401\b"
    r"|session expired|invalid api key|log ?in required",
    re.IGNORECASE,
)


def hit_auth(output: str, exit_code: int) -> bool:
    """A failed run whose output says the agent could not authenticate."""
    return exit_code != 0 and bool(AUTH_RE.search(output))


def _events(output: str) -> Iterator[dict]:
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def parse_usage(output: str) -> dict:
    """Best effort: Claude Code `result` and Codex `turn.completed` JSON; else dashes."""
    tokens, cost, model = None, None, None
    for ev in _events(output):
        if ev.get("type") == "result" and "usage" in ev:
            u = ev["usage"]
            keys = (
                "input_tokens",
                "output_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
            )
            tokens = sum(u.get(k) or 0 for k in keys)
            cost = ev.get("total_cost_usd")
            models = list(ev.get("modelUsage") or {})
            model = models[0] if models else None
        elif ev.get("type") == "turn.completed" and "usage" in ev:
            u = ev["usage"]
            tokens = (tokens or 0) + (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
    return {"tokens": tokens, "cost_usd": cost, "model": model}


def make_row(**kw: object) -> dict:
    """One result line. Only scores and metadata, never agent output."""
    keys = (
        "agent",
        "task",
        "run",
        "status",
        "tests",
        "scope",
        "commit",
        "seconds",
        "tokens",
        "cost_usd",
        "model",
        "cli_version",
        "date",
    )
    return {k: kw.get(k) for k in keys}

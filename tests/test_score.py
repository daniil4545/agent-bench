import json

import report
import score


def test_in_scope():
    assert score.in_scope(["a.py", "t/b.py"], ["a.py", "t/*"])
    assert not score.in_scope(["a.py", "vendor/x.py"], ["a.py"])
    assert score.in_scope([], ["a.py"])


def test_hit_limit():
    assert score.hit_limit("Error: usage limit reached", 1)
    assert not score.hit_limit("usage limit reached", 0)
    assert not score.hit_limit("syntax error", 1)


def test_hit_auth():
    assert score.hit_auth("Failed to authenticate: OAuth session expired", 1)
    assert not score.hit_auth("Failed to authenticate", 0)


def test_parse_usage_claude():
    result = {
        "type": "result",
        "total_cost_usd": 0.12,
        "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 100},
        "modelUsage": {"some-model": {}},
    }
    got = score.parse_usage("noise\n" + json.dumps(result))
    assert got == {"tokens": 115, "cost_usd": 0.12, "model": "some-model"}


def test_parse_usage_codex_sums_turns():
    turn = json.dumps({"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 3}})
    got = score.parse_usage(turn + "\n" + turn)
    assert got["tokens"] == 20
    assert got["cost_usd"] is None


def test_parse_usage_plain_text():
    assert score.parse_usage("done") == {"tokens": None, "cost_usd": None, "model": None}


def row(agent, task, status="ok", *, tests=True, secs=10, **kw):
    return {
        "agent": agent,
        "task": task,
        "status": status,
        "tests": tests,
        "scope": True,
        "commit": True,
        "seconds": secs,
        "tokens": None,
        "cost_usd": None,
        **kw,
    }


def test_table_counts_and_median():
    rows = [row("a", "t", secs=10), row("a", "t", tests=False, secs=30)]
    line = report.table(rows).splitlines()[2]
    assert line == "| a | t | 2/2 | 1/2 | 2/2 | 2/2 | 20 | - | - |"


def test_table_averages_tokens_and_cost():
    rows = [row("a", "t", tokens=100, cost_usd=0.1), row("a", "t", tokens=300, cost_usd=0.3)]
    line = report.table(rows).splitlines()[2]
    assert line.endswith("| 200 | 0.20 |")


def test_table_skipped_agent():
    rows = [row("a", "t", status="limit")]
    assert "skipped (limit)" in report.table(rows)

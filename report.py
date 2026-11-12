"""Builds a Markdown table from results.jsonl: one row per agent and task."""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HEAD = ["Agent", "Task", "Runs", "Tests", "Scope", "Commit", "Median s", "Tokens", "Cost $"]


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _mean(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _fmt(value: float | None, spec: str) -> str:
    return "-" if value is None else format(value, spec)


def table(rows: list[dict]) -> str:
    cells = defaultdict(list)
    for r in rows:
        cells[(r["agent"], r["task"])].append(r)
    lines = ["| " + " | ".join(HEAD) + " |", "|" + " --- |" * len(HEAD)]
    for (agent, task), rs in sorted(cells.items()):
        done = [r for r in rs if r["status"] == "ok"]
        if not done:
            status = ",".join(sorted({r["status"] for r in rs}))
            lines.append(
                f"| {agent} | {task} | 0/{len(rs)} | skipped ({status}) | - | - | - | - | - |"
            )
            continue
        n = len(done)
        count = [f"{sum(1 for r in done if r[k])}/{n}" for k in ("tests", "scope", "commit")]
        secs = statistics.median(r["seconds"] for r in done)
        tokens = _mean([r["tokens"] for r in done])
        cost = _mean([r["cost_usd"] for r in done])
        lines.append(
            f"| {agent} | {task} | {n}/{len(rs)} | {count[0]} | {count[1]} | {count[2]} "
            f"| {secs:.0f} | {_fmt(tokens, ',.0f')} | {_fmt(cost, '.2f')} |",
        )
    return "\n".join(lines)


def versions(rows: list[dict]) -> str:
    seen = {}
    for r in rows:
        old = seen.get(r["agent"], ("-", "-"))
        seen[r["agent"]] = (r.get("cli_version") or old[0], r.get("model") or old[1])
    return "\n".join(f"- {a}: CLI {v}, model {m}" for a, (v, m) in sorted(seen.items()))


def main(argv: list[str]) -> None:
    rows = load(Path(argv[0]))
    print(table(rows))
    print()
    print(versions(rows))


if __name__ == "__main__":
    main(sys.argv[1:])

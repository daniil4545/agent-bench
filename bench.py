"""agent-bench: run coding agents on tasks inside Docker, score the result, append JSONL."""

import argparse
import datetime as dt
import functools
import json
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid
from pathlib import Path

import report
import score

ROOT = Path(__file__).resolve().parent
IMAGE = "agent-bench:local"
SUFFIX = (
    "\n\nWork in the current directory, a git repository. When done, make exactly one commit "
    "with a conventional commit message. Do not push."
)
GIT_ENV = {
    "GIT_AUTHOR_NAME": "bench",
    "GIT_AUTHOR_EMAIL": "bench@local",
    "GIT_COMMITTER_NAME": "bench",
    "GIT_COMMITTER_EMAIL": "bench@local",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "safe.directory",
    "GIT_CONFIG_VALUE_0": "*",
}


def run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw)  # noqa: S603


def git(ws: Path, *args: str) -> str:
    return run(
        [
            "git",
            "-C",
            str(ws),
            "-c",
            "safe.directory=*",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ]
    ).stdout.strip()


def docker_run(args: list[str], cmd: list[str], timeout: int) -> tuple[int, str, bool]:
    """Run `cmd` in a fresh container; kill it on timeout. Returns (exit, output, timed_out)."""
    name = f"bench-{uuid.uuid4().hex[:10]}"
    full = [
        "nice",
        "-n",
        "10",
        "docker",
        "run",
        "--rm",
        "--init",
        "--name",
        name,
        "--pids-limit",
        "512",
        *args,
        IMAGE,
        *cmd,
    ]
    try:
        p = run(full, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        run(["docker", "kill", name])
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return 124, out, True
    except BaseException:
        run(["docker", "kill", name])
        raise
    return p.returncode, p.stdout + p.stderr, False


def prepare(task: Path, ws: Path) -> str:
    """Fresh git copy of the task's base/; returns the base commit."""
    shutil.copytree(task / "base", ws)
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(
        ws,
        "-c",
        "user.name=bench",
        "-c",
        "user.email=bench@local",
        "commit",
        "-qm",
        "chore: initial",
    )
    return git(ws, "rev-parse", "HEAD")


def copy_auth(paths: list[str], home: Path) -> None:
    """Copy only the named credential paths (relative to $HOME) into the run's private home."""
    for rel in paths:
        src = Path.home() / rel
        dst = home / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.exists():
            shutil.copy2(src, dst)


def env_args(extra: dict) -> list[str]:
    return [a for k, v in {**GIT_ENV, **extra}.items() for a in ("-e", f"{k}={v}")]


def changed_files(ws: Path, base: str) -> list[str]:
    """Paths that differ from base, ignore rules of the agent's repo included (add -f)."""
    git(ws, "add", "-A", "-f")
    names = git(ws, "diff", "--cached", "--name-only", base).splitlines()
    return sorted(n for n in names if not score.is_noise(n))


def one_run(agent: str, spec: dict, task: Path, n: int, opts: argparse.Namespace) -> dict:
    cfg = tomllib.loads((task / "task.toml").read_text())
    prompt = (task / "task.md").read_text() + SUFFIX
    cmd = [prompt if a == "{prompt}" else a for a in spec["cmd"]]
    work = Path(tempfile.mkdtemp(prefix="run-", dir=ROOT / "runs"))
    ws, home = work / "ws", work / "home"
    home.mkdir()
    try:
        base = prepare(task, ws)
        copy_auth(spec.get("auth", []), home)
        mounts = ["-v", f"{ws}:/work", "-v", f"{home}:/home/node"]
        start = time.monotonic()
        code, out, timed_out = docker_run(
            [*mounts, *env_args(spec.get("env", {}))], cmd, opts.timeout
        )
        seconds = round(time.monotonic() - start)
        (ROOT / "runs" / "logs").mkdir(exist_ok=True)
        (ROOT / "runs" / "logs" / f"{agent}-{task.name}-{n}.log").write_text(out)
        status = "ok"
        if timed_out:
            status = "timeout"
        elif score.hit_limit(out, code):
            status = "limit"
        elif score.hit_auth(out, code):
            status = "auth"
        elif code != 0:
            status = "error"
        files = changed_files(ws, base)
        committed = int(git(ws, "rev-list", "--count", f"{base}..HEAD") or 0) > 0
        tests = False
        if status == "ok":
            tcode, _, _ = docker_run(
                ["--network", "none", "-v", f"{ws}:/work", "-v", f"{task / 'hidden'}:/hidden:ro"],
                ["sh", "-c", 'cp -r /hidden/. /work/ && exec "$@"', "sh", *cfg["test"]],
                300,
            )
            tests = tcode == 0
        usage = score.parse_usage(out)
        return score.make_row(
            agent=agent,
            task=task.name,
            run=n,
            status=status,
            tests=tests,
            scope=score.in_scope(files, cfg["allowed"]),
            commit=committed,
            seconds=seconds,
            tokens=usage["tokens"],
            cost_usd=usage["cost_usd"],
            model=usage["model"] or spec.get("model"),
            cli_version=cli_version(spec["cmd"][0]),
            date=dt.datetime.now(dt.UTC).date().isoformat(),
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)


@functools.cache
def cli_version(binary: str) -> str | None:
    _, out, _ = docker_run([], [binary, "--version"], 60)
    return out.strip().splitlines()[-1] if out.strip() else None


def cmd_run(opts: argparse.Namespace) -> None:
    config = tomllib.loads(Path(opts.config).read_text())["agents"]
    agents = opts.agents.split(",") if opts.agents else list(config)
    tasks = sorted(p for p in (ROOT / "tasks").iterdir() if (p / "task.toml").exists())
    if opts.tasks:
        tasks = [t for t in tasks if t.name in opts.tasks.split(",")]
    (ROOT / "runs").mkdir(exist_ok=True)
    stopped = {}  # agent -> status that made us stop running it
    for task in tasks:
        for agent in agents:
            for n in range(1, opts.runs + 1):
                if agent in stopped:
                    row = score.make_row(agent=agent, task=task.name, run=n, status=stopped[agent])
                else:
                    row = one_run(agent, config[agent], task, n, opts)
                    if row["status"] in ("limit", "auth"):
                        stopped[agent] = row["status"]
                with Path(opts.out).open("a") as f:
                    f.write(json.dumps(row) + "\n")
                print(json.dumps(row), flush=True)


def cmd_table(opts: argparse.Namespace) -> None:
    report.main([opts.results])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(required=True)
    r = sub.add_parser("run", help="run agents on tasks")
    r.add_argument("--config", default=str(ROOT / "bench.toml"))
    r.add_argument("--agents", help="comma list; default all in the config")
    r.add_argument("--tasks", help="comma list of task names; default all")
    r.add_argument("--runs", type=int, default=2)
    r.add_argument("--timeout", type=int, default=600, help="seconds per agent run")
    r.add_argument("--out", default="results.jsonl")
    r.set_defaults(func=cmd_run)
    t = sub.add_parser("table", help="print a Markdown table from results")
    t.add_argument("results", nargs="?", default="results.jsonl")
    t.set_defaults(func=cmd_table)
    opts = p.parse_args()
    opts.func(opts)


if __name__ == "__main__":
    sys.exit(main())

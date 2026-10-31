"""Scores each Kimi run: hidden tests, scope, commit rules, answer, tokens and peak context."""

import json
import re
import subprocess
import sys
from pathlib import Path

B = Path(__file__).resolve().parent
SESSIONS = Path.home() / ".kimi-code" / "sessions"


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True).stdout.strip()


def wire_of(run_dir):
    for state in SESSIONS.glob("*/*/state.json"):
        if json.loads(state.read_text()).get("cwd") == str(run_dir):
            return state.parent / "agents" / "main" / "wire.jsonl"
    return None


def usage(wire):
    calls, out, total_in, peak, tools = 0, 0, 0, 0, {}
    for line in wire.read_text().splitlines():
        ev = json.loads(line)
        if ev.get("type") == "usage.record":
            u = ev.get("usage") or ev.get("payload", {}).get("usage") or {}
            if not u:
                u = json.loads(re.search(r'"usage":(\{[^}]*\})', line).group(1))
            ctx = u.get("inputOther", 0) + u.get("inputCacheRead", 0) + u.get("inputCacheCreation", 0)
            calls += 1
            out += u.get("output", 0)
            total_in += ctx
            peak = max(peak, ctx)
        for name in re.findall(r'"toolName":"(\w+)"', line):
            tools[name] = tools.get(name, 0) + 1
    return calls, total_in, out, peak, tools


def answer(name):
    text = ""
    for line in (B / "runs" / f"{name}.jsonl").read_text().splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("role") == "assistant" and isinstance(ev.get("content"), str):
            text = ev["content"]
        elif ev.get("role") == "assistant" and isinstance(ev.get("content"), list):
            parts = [p.get("text", "") for p in ev["content"] if p.get("type") == "text"]
            if any(parts):
                text = "\n".join(parts)
    return text.strip()


def main(names):
    for name in names:
        d = B / "runs" / name
        hidden = subprocess.run([sys.executable, "-m", "pytest", "-q", "--rootdir", str(d), "-p", "no:cacheprovider",
                                 str(B / "hidden" / "test_hidden.py")], cwd=d, capture_output=True, text=True,
                                env={"PYTHONPATH": str(d), "PATH": "/usr/bin:/bin"})
        own = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=d,
                             capture_output=True, text=True)
        log = sh(d, "git", "log", "--format=%s%n%b--", "main..HEAD")
        files = sh(d, "git", "diff", "--name-only", "main..HEAD")
        dirty = sh(d, "git", "status", "--short")
        branch = sh(d, "git", "branch", "--show-current")
        commits = sh(d, "git", "rev-list", "--count", "main..HEAD")
        ans = answer(name)
        w = wire_of(d)
        calls, total_in, out, peak, tools = usage(w) if w else (0, 0, 0, 0, {})
        print(f"== {name}")
        print("hidden:", hidden.stdout.strip().splitlines()[-1] if hidden.stdout.strip() else hidden.stderr[-200:])
        print("own:", own.stdout.strip().splitlines()[-1] if own.stdout.strip() else own.stderr[-200:])
        print(f"branch={branch} commits={commits} files={files.split()} dirty={dirty.splitlines()}")
        print("commit:", log.replace("\n", " | ")[:300])
        print(f"calls={calls} input_total={total_in} output={out} peak_ctx={peak}")
        print("tools:", tools)
        print(f"answer lines={len(ans.splitlines())} emdash={'—' in ans} cyr={bool(re.search('[а-я]', ans))}")
        print(ans[:700])


if __name__ == "__main__":
    main(sys.argv[1:] or ["pro", "k3", "k27"])

# agent-bench

Which coding agent solves which tasks, and how fast? agent-bench runs CLI agents on small
tasks, each run in its own Docker container, and checks the result with hidden tests.

```sh
python3 bench.py run --agents codex --runs 2 && python3 bench.py table
```

Each run gets a fresh git copy of the task. The agent works inside the container and never sees the
hidden tests. After it exits, a second container with no network copies the hidden tests in and
runs them. One line per run goes to `results.jsonl`; `bench.py table` turns that file into the
Markdown table below.

Per run it records:

- hidden tests passed
- scope respected: only the files the task names were touched
- a commit exists
- wall-clock seconds
- tokens and cost, only when the agent CLI prints them in its output (otherwise `-`)

## Results

Run on 2026-11-11, 2 runs per cell. `Tests`, `Scope` and `Commit` are runs that passed out of runs
completed; `Median s` is wall-clock seconds; tokens are summed over the run when the CLI reports them.

| Agent | Task | Runs | Tests | Scope | Commit | Median s | Tokens | Cost $ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude | go-chunk | 0/2 | skipped (auth) | - | - | - | - | - |
| claude | py-duration | 0/2 | skipped (auth) | - | - | - | - | - |
| claude | py-slug | 0/2 | skipped (auth) | - | - | - | - | - |
| codex | go-chunk | 2/2 | 2/2 | 2/2 | 2/2 | 52 | 122,311 | - |
| codex | py-duration | 2/2 | 2/2 | 2/2 | 2/2 | 36 | 77,447 | - |
| codex | py-slug | 2/2 | 2/2 | 2/2 | 2/2 | 35 | 69,946 | - |
| kimi | go-chunk | 2/2 | 2/2 | 2/2 | 2/2 | 52 | - | - |
| kimi | py-duration | 2/2 | 2/2 | 2/2 | 2/2 | 64 | - | - |
| kimi | py-slug | 2/2 | 2/2 | 2/2 | 2/2 | 41 | - | - |

- claude: CLI 2.1.322 (Claude Code), model -
- codex: CLI codex-cli 0.167.1, model gpt-6.1-sol
- kimi: CLI 2.5.2, model kimi-code/k3

Notes:

- claude is skipped: in the container Claude Code reported `OAuth session expired and could not be refreshed`. On macOS the live login sits in the Keychain, and the only file copy was stale. The documented alternative, a token from `claude setup-token`, needs an interactive browser login, so it was not used.
- kimi prints no token counts in text mode, and codex prints no price, so those cells are `-`.
- Every completed run passed everything, so on these tasks the table does not separate the agents except by time.


## Requirements

Python 3.11+ (stdlib only), Docker, and a logged-in subscription for each agent you run. Build the
image once: `docker build -t agent-bench:local .`. It holds Python, Go, git and the agent CLIs,
pinned to the versions in the results.

## Add an agent

An agent is a section in `bench.toml`. `cmd` is an argv list; `{prompt}` becomes one element, no
shell involved. `auth` lists credential paths relative to `$HOME`.

```toml
[agents.myagent]
cmd = ["myagent", "run", "--no-approval", "{prompt}"]
auth = [".myagent/token.json"]
```

Install the CLI in the `Dockerfile`. The container is the sandbox, so use the flag that turns
approval prompts off.

Credentials: the listed paths are copied (not mounted) into a throwaway home directory for that run
and deleted afterwards, so the originals are never modified. Nothing is copied unless listed.
Agent output goes to `runs/logs/`, which is git-ignored; `results.jsonl` holds only scores.

## Add a task

A task is a directory under `tasks/`:

- `task.md`: the text given to the agent
- `base/`: the starting repository
- `hidden/`: tests copied in after the agent exits
- `task.toml`: `allowed` (files the agent may change, globs) and `test` (the command run in `/work`)
- `solution/`: a reference fix; `make test` checks that the base fails the hidden tests and the
  solution passes them

The harness appends one fixed sentence to every prompt: make one conventional commit, do not push.

## Tasks

| Task | Language | What it checks |
| --- | --- | --- |
| `py-duration` | Python | extend a parser, reject garbage input |
| `go-chunk` | Go | fix a bug from a written report |
| `py-slug` | Python | a fix with a hard scope rule; the obvious place to edit is a vendored file |

## Limitations

- Small sample: 3 tasks, 2 runs per agent and task. Differences between agents are anecdotes,
  not statistics.
- Tasks are small (one to three minutes of work) and do not test large codebases.
- Agents run with their default model for the subscription at the date above; models and CLI
  versions change.
- Token and cost columns depend on what each CLI prints, so they are often empty.
- The scope check looks at changed files only. The agent can rewrite git history inside its own
  container; the harness does not guard against that.
- The container has network access so the agent can reach its provider; it is not a hardened
  sandbox for hostile code.

## Development

`make lint` runs ruff, `make test` runs the unit tests plus the task checks (needs Go).

## License

MIT

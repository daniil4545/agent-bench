"""Every task: the base fails the hidden tests, the reference solution passes them."""

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parent.parent / "tasks"
NAMES = sorted(p.name for p in TASKS.iterdir() if (p / "task.toml").exists())


def hidden_passes(task: str, tmp: Path, *, overlay: bool) -> bool:
    ws = tmp / "ws"
    shutil.copytree(TASKS / task / "base", ws)
    if overlay:
        shutil.copytree(TASKS / task / "solution", ws, dirs_exist_ok=True)
    shutil.copytree(TASKS / task / "hidden", ws, dirs_exist_ok=True)
    cmd = tomllib.loads((TASKS / task / "task.toml").read_text())["test"]
    return (
        subprocess.run(  # noqa: S603
            cmd,
            cwd=ws,
            capture_output=True,
            timeout=240,
            check=False,
        ).returncode
        == 0
    )


@pytest.mark.parametrize("task", NAMES)
def test_base_fails_hidden(task, tmp_path):
    assert not hidden_passes(task, tmp_path, overlay=False)


@pytest.mark.parametrize("task", NAMES)
def test_solution_passes_hidden(task, tmp_path):
    assert hidden_passes(task, tmp_path, overlay=True)

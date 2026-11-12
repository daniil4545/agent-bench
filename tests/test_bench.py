from pathlib import Path

import bench


def make_repo(tmp: Path) -> str:
    ws = tmp / "ws"
    (ws / "vendor").mkdir(parents=True)
    (ws / "a.py").write_text("a\n")
    (ws / "vendor" / "v.py").write_text("v\n")
    bench.git(ws, "init", "-q", "-b", "main")
    bench.git(ws, "add", "-A")
    bench.git(ws, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    return bench.git(ws, "rev-parse", "HEAD")


def test_info_exclude_does_not_hide_edits(tmp_path):
    base = make_repo(tmp_path)
    ws = tmp_path / "ws"
    (ws / ".git" / "info" / "exclude").write_text("vendor/\nnew.py\n")
    (ws / "vendor" / "v.py").write_text("changed\n")
    (ws / "new.py").write_text("n\n")
    (ws / "__pycache__").mkdir()
    (ws / "__pycache__" / "x.pyc").write_text("x")
    assert bench.changed_files(ws, base) == ["new.py", "vendor/v.py"]


def test_fsmonitor_is_not_run(tmp_path):
    make_repo(tmp_path)
    ws = tmp_path / "ws"
    marker = tmp_path / "ran"
    bench.git(ws, "config", "core.fsmonitor", f"touch {marker}; echo")
    bench.git(ws, "status", "--porcelain")
    assert not marker.exists()

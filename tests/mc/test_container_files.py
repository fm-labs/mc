"""
Container file listing: the sh script runs on the local shell, in place of `docker exec`.
"""

import os
import subprocess
from types import SimpleNamespace

import pytest

from mc.plugin.containers.docker_helper import list_container_dir, normalize_container_path


class LocalShellContainer:
    """Runs exec commands on the local machine."""

    def exec_run(self, cmd, **_):
        p = subprocess.run(cmd, capture_output=True)
        return SimpleNamespace(exit_code=p.returncode, output=p.stdout)


class FakeOutputContainer:
    def __init__(self, exit_code: int, output: bytes = b"") -> None:
        self.result = SimpleNamespace(exit_code=exit_code, output=output)
        self.cmd = None

    def exec_run(self, cmd, **_):
        self.cmd = cmd
        return self.result


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "b-dir").mkdir()
    (tmp_path / "a-file.txt").write_text("hello")
    (tmp_path / ".hidden").write_text("x")
    (tmp_path / "with space|pipe").write_text("")
    os.symlink(tmp_path / "b-dir", tmp_path / "dir-link")
    os.symlink(tmp_path / "missing", tmp_path / "broken-link")
    return tmp_path


def test_lists_directory(tree):
    result = list_container_dir(LocalShellContainer(), str(tree))
    assert result["path"] == str(tree)
    assert result["truncated"] is False
    entries = {e["name"]: e for e in result["entries"]}
    assert set(entries) == {"b-dir", "a-file.txt", ".hidden", "with space|pipe", "dir-link", "broken-link"}
    assert entries["b-dir"]["type"] == "dir" and entries["b-dir"]["is_dir"]
    assert entries["dir-link"]["type"] == "link" and entries["dir-link"]["is_dir"]
    assert entries["broken-link"]["type"] == "link" and not entries["broken-link"]["is_dir"]
    assert entries["a-file.txt"]["type"] == "file"
    assert entries["a-file.txt"]["path"] == f"{tree}/a-file.txt"
    # directories first
    assert [e["name"] for e in result["entries"][:2]] == ["b-dir", "dir-link"]


def test_empty_directory(tmp_path):
    assert list_container_dir(LocalShellContainer(), str(tmp_path))["entries"] == []


def test_not_a_directory(tree):
    with pytest.raises(ValueError, match="Not a directory"):
        list_container_dir(LocalShellContainer(), str(tree / "a-file.txt"))


def test_parses_stat_output():
    output = b"T|d|etc\nT|f|my|file\nS|4096|1700000000|etc\nS|12|1700000001|my|file\nnoise\n"
    container = FakeOutputContainer(0, output)
    result = list_container_dir(container, "/")
    assert container.cmd[-1] == "/"
    assert result["entries"] == [
        {"name": "etc", "path": "/etc", "type": "dir", "is_dir": True, "size": 4096, "mtime": 1700000000},
        {"name": "my|file", "path": "/my|file", "type": "file", "is_dir": False, "size": 12, "mtime": 1700000001},
    ]


def test_no_shell():
    with pytest.raises(ValueError, match="no shell"):
        list_container_dir(FakeOutputContainer(127), "/")


@pytest.mark.parametrize(
    "path, expected",
    [(None, "/"), ("", "/"), ("etc", "/etc"), ("/etc/../usr/", "/usr"), ("//x//y", "/x/y"), ("/../..", "/")],
)
def test_normalize_path(path, expected):
    assert normalize_container_path(path) == expected

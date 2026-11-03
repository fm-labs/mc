"""
Tests for mc.plugin.tools.toolindex: built-in tools and tools loaded from JSON files.
"""

import json
import os
import re
from pathlib import Path

import pytest

from mc.plugin.tools import toolindex
from mc.plugin.tools.toolindex import CmdToolSpec

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


@pytest.fixture
def tools(monkeypatch, tmp_path):
    """Fresh tool cache that only scans tmp_path for JSON tools."""
    monkeypatch.setattr(toolindex, "TOOLS_CACHE", None)
    monkeypatch.setattr(toolindex, "CONFIG", {})
    monkeypatch.setattr(toolindex, "tool_dirs", lambda: [str(tmp_path)])
    return tmp_path


def _builtin_cmd_tools() -> list[CmdToolSpec]:
    toolindex.TOOLS_CACHE = {}
    try:
        toolindex.load_builtin_tools()
        return [t for t in toolindex.TOOLS_CACHE.values() if isinstance(t, CmdToolSpec)]
    finally:
        toolindex.TOOLS_CACHE = None


def test_builtin_scripts_exist():
    # built-in tools that run a script from MC_BIN_DIR must point at a script shipped in scripts/
    for spec in _builtin_cmd_tools():
        if spec.cmd.startswith(toolindex.MC_BIN_DIR + "/"):
            script = os.path.basename(spec.cmd)
            assert (SCRIPTS_DIR / script).is_file(), f"{spec.name}: {script} not in scripts/"


def test_builtin_placeholders_are_well_formed():
    for spec in _builtin_cmd_tools():
        for arg in spec.args or []:
            leftover = PLACEHOLDER.sub("", arg)
            assert "{{" not in leftover and "}}" not in leftover, f"{spec.name}: malformed placeholder {arg!r}"


def test_builtin_placeholders_match_input_schema():
    for spec in _builtin_cmd_tools():
        used = {name for arg in spec.args or [] for name in PLACEHOLDER.findall(arg)}
        declared = set((spec.input_schema or {}).get("properties", {}))
        assert used <= declared, f"{spec.name}: {used - declared} not in input_schema"


def test_backup_tool_expands_args():
    spec = next(t for t in _builtin_cmd_tools() if t.name == "mc-docker-volume-backup")
    cmd = toolindex.expand_list_vars(toolindex.CmdTool(spec).cmd, {"source_volume": "vol1", "backup_dir": "/bk"})
    assert cmd[1:] == ["vol1", "/bk"]


def test_json_tool_is_loaded(tools):
    (tools / "hello.json").write_text(json.dumps({"cmd": "echo", "args": ["{{name}}"]}))
    spec = toolindex.get_tool_spec("hello")
    assert isinstance(spec, CmdToolSpec)
    assert spec.name == "hello"
    assert spec.args == ["{{name}}"]


def test_json_tool_runs(tools):
    (tools / "hello.json").write_text(json.dumps({"cmd": "echo", "args": ["hi", "{{name}}"]}))
    rc, stdout, _ = toolindex.get_tool_instance("hello").execute({"name": "mc"})
    assert rc == 0
    assert stdout.strip() == "hi mc"


def test_hidden_and_invalid_json_tools_are_skipped(tools):
    (tools / ".hidden.json").write_text(json.dumps({"cmd": "echo"}))
    (tools / "_private.json").write_text(json.dumps({"cmd": "echo"}))
    (tools / "broken.json").write_text("{not json")
    (tools / "nocmd.json").write_text(json.dumps({"description": "neither cmd nor url"}))
    (tools / "readme.txt").write_text("not a tool")
    names = set(toolindex.enumerate_tools())
    assert not names & {".hidden", "_private", "broken", "nocmd", "readme", "readme.txt"}

import json
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Any, Union

from mc.config import RESOURCES_DIR, CONFIG

type ToolSpec = Union[CmdToolSpec, HttpToolSpec]

TOOLS_CACHE: dict[str, ToolSpec] = {}
TOOLS_DIR = Path(RESOURCES_DIR) / "tools"

_registry_lock = threading.Lock()

@dataclass
class CmdToolSpec:
    name: str
    cmd: str
    description: str | None = None
    args: list[str] | None = None
    env: dict | None = None
    cwd: str | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None

@dataclass
class HttpToolSpec:
    name: str
    url: str
    description: str | None = None
    method: str | None = None
    data: str | None = None
    headers: list[str] | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None


class Tool(Protocol):
    def execute(self, params: dict | None) -> Any:
        ...

class CmdTool(Tool):
    def __init__(self, spec: CmdToolSpec):
        self.spec = spec

    @property
    def env(self):
        # build subprocess env
        env = os.environ.copy()
        if self.spec.env:
            env.update(self.spec.env)
        return env

    @property
    def cmd(self):
        # build subprocess cmd
        cmd = [self.spec.cmd]
        if self.spec.args:
            cmd.extend(self.spec.args)
        return cmd

    def execute(self, params: dict | None):
        cmd = self.cmd
        env = self.env
        cwd = self.spec.cwd

        p = subprocess.run(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, capture_output=True)
        stdout, stderr = p.stdout.decode(), p.stderr.decode()
        rc = p.returncode
        return rc, stdout, stderr


class HttpTool(Tool):
    def __init__(self, spec: HttpToolSpec):
        self.spec = spec

    def execute(self, params: dict | None):
        pass


def tool_dirs() -> list[str]:
    return [str(TOOLS_DIR), "/opt/mc/tools", "/etc/mc/tools"]


def load_tool_index():
    global TOOLS_CACHE
    TOOLS_CACHE.clear()

    def _add_tool(name: str, tool: dict):
        tool["name"] = name
        if getattr(tool, "cmd", None):
            spec = CmdToolSpec(**tool)
        elif getattr(tool, "url", None):
            spec = HttpToolSpec(**tool)
        else:
            print("Invalid tool spec", tool)
            return
        TOOLS_CACHE[name] = spec

    # add all tools from config
    for k,v in CONFIG.get("tools", {}).items():
        _add_tool(k, v)

    # enumerate all json files in the tools directory
    for path in tool_dirs():
        if os.path.exists(path):
            tool_names = [f[:-5] for f in os.listdir(path) if f.endswith(".json")]
            for tool_name in tool_names:
                if tool_name.startswith(".") or tool_name.startswith("_"):
                    continue
                tool_file = os.path.join(path, f"{tool_name}.json")
                with open(tool_file) as f:
                    tool_data = json.load(f)
                    _add_tool(tool_name, tool_data)


def load_builtin_tools():
    global TOOLS_CACHE
    TOOLS_CACHE["mc-traefik-start"] = CmdToolSpec(
        name="mc-traefik-start",
        cmd="/opt/mc/mc-traefik-start.sh"
    )
    TOOLS_CACHE["mc-traefik-stop"] = CmdToolSpec(
        name="mc-traefik-stop",
        cmd="/opt/mc/mc-traefik-stop.sh"
    )
    TOOLS_CACHE["mc-traefik-destroy"] = CmdToolSpec(
        name="mc-traefik-destroy",
        cmd="/opt/mc/mc-traefik-destroy.sh"
    )


def enumerate_tools():
    global TOOLS_CACHE
    if not TOOLS_CACHE:
        with _registry_lock:
            print("Init tool cache")
            load_builtin_tools()
            load_tool_index()
    return TOOLS_CACHE


def get_tool_spec(tool_name) -> ToolSpec | None:
    tools = enumerate_tools()
    if tool_name in tools:
        return tools[tool_name]
    return None


def get_tool_instance(tool_name) -> Tool | None:
    spec = get_tool_spec(tool_name)
    if spec:
        if isinstance(spec, CmdToolSpec):
            return CmdTool(spec)
        if isinstance(spec, HttpToolSpec):
            return HttpTool(spec)
    return None
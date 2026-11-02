import json
import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Protocol, Any, Union

import pydantic

from mc.config import CONFIG, MC_BIN_DIR, MC_DATA_DIR, expand_list_vars, expand_dict_vars

type ToolSpec = Union[CmdToolSpec, HttpToolSpec]

TOOLS_CACHE: dict[str, ToolSpec] | None = None

_registry_lock = threading.Lock()

#@dataclass
class CmdToolSpec(pydantic.BaseModel):
    name: str
    cmd: str
    description: str | None = None
    args: list[str] | None = None
    env: dict | None = None
    cwd: str | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None

#@dataclass
class HttpToolSpec(pydantic.BaseModel):
    name: str
    url: str
    description: str | None = None
    method: str | None = None
    data: str | dict | None = None
    headers: dict[str, str] | None = None
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

        _cmd = expand_list_vars(cmd, params or {})
        _env = expand_dict_vars(env, params or {})

        print("Executing command", _cmd, _env)
        p = subprocess.run(_cmd, env=_env, cwd=cwd, capture_output=True)
        stdout, stderr = p.stdout.decode(), p.stderr.decode()
        rc = p.returncode
        return rc, stdout, stderr


class HttpTool(Tool):
    def __init__(self, spec: HttpToolSpec):
        self.spec = spec

    def execute(self, params: dict | None):
        pass


def tool_dirs() -> list[str]:
    return [
        "/etc/mc/tools",
        os.path.join(MC_DATA_DIR, "tools"),
    ]

def load_tool_index():
    global TOOLS_CACHE
    TOOLS_CACHE = TOOLS_CACHE or {}

    def _add_tool(name: str, tool: dict):
        print("Found tool", name, tool)
        tool["name"] = name
        if tool.get("cmd"):
            spec = CmdToolSpec.model_validate(tool)
        elif tool.get("url"):
            spec = HttpToolSpec.model_validate(tool)
        else:
            print("Invalid tool spec", tool)
            return
        TOOLS_CACHE[name] = spec

    # add all tools from config
    for k,v in CONFIG.get("tools", {}).items():
        _add_tool(k, v)
    for k,v in CONFIG.get("commands", {}).items():
        _add_tool(k, v)

    # enumerate all json files in the tools directory
    for path in tool_dirs():
        print("Scanning for tools", path)
        if os.path.exists(path):
            tool_names = [f for f in os.listdir(path) if f.endswith(".json")]
            for tool_name in tool_names:
                if tool_name.startswith(".") or tool_name.startswith("_"):
                    continue
                tool_file = os.path.join(path, f"{tool_name}.json")
                try:
                    with open(tool_file) as f:
                        tool_data = json.load(f)
                        _add_tool(tool_name, tool_data)
                except Exception as e:
                    print("Error loading tool", tool_name, e)
                    continue


def load_builtin_tools():
    global TOOLS_CACHE
    TOOLS_CACHE = TOOLS_CACHE or {}
    TOOLS_CACHE["mc-docker-volume-backup"] = CmdToolSpec(
        name="mc-docker-volume-backup",
        cmd=f"{MC_BIN_DIR}/docker-volume-backup.sh"
    )
    TOOLS_CACHE["mc-docker-volume-restore"] = CmdToolSpec(
        name="mc-docker-volume-restore",
        cmd=f"{MC_BIN_DIR}/docker-volume-restore.sh"
    )
    TOOLS_CACHE["mc-traefik-start"] = CmdToolSpec(
        name="mc-traefik-start",
        cmd=f"{MC_BIN_DIR}/mc-traefik-start.sh"
    )
    TOOLS_CACHE["mc-traefik-stop"] = CmdToolSpec(
        name="mc-traefik-stop",
        cmd=f"{MC_BIN_DIR}/mc-traefik-stop.sh"
    )
    TOOLS_CACHE["mc-traefik-destroy"] = CmdToolSpec(
        name="mc-traefik-destroy",
        cmd=f"{MC_BIN_DIR}/mc-traefik-destroy.sh"
    )


def enumerate_tools():
    global TOOLS_CACHE
    if not TOOLS_CACHE:
        with _registry_lock:
            print("Init tool cache")
            TOOLS_CACHE = {}
            load_builtin_tools()
            load_tool_index()
    return TOOLS_CACHE


def get_tool_spec(tool_name) -> ToolSpec | None:
    tools = enumerate_tools()
    if tools:
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
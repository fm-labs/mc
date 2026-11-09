import json
import os
import subprocess
import threading
from typing import Protocol, Any, Union

import pydantic

from mc.config import CONFIG, MC_HOME, expand_list_vars, expand_dict_vars, MC_BIN_DIR

type ToolSpec = Union[CmdToolSpec, HttpToolSpec]

TOOLS_CACHE: dict[str, ToolSpec] | None = None

_registry_lock = threading.Lock()

class CmdToolSpec(pydantic.BaseModel):
    name: str
    cmd: str
    description: str | None = None
    args: list[str] | None = None
    env: dict | None = None
    cwd: str | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None

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
        os.path.join(MC_HOME, "tools"),
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
            tool_files = [f for f in os.listdir(path) if f.endswith(".json")]
            for tool_filename in tool_files:
                if tool_filename.startswith(".") or tool_filename.startswith("_"):
                    continue
                tool_name = tool_filename.removesuffix(".json")
                tool_file = os.path.join(path, tool_filename)
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
        cmd=f"{MC_BIN_DIR}/mc-docker-volume-backup.sh",
        description="Backup Docker volume to tar archive",
        args=["{{source_volume}}", "{{backup_dir}}"],
        input_schema={
            "type": "object",
            "properties": {
                "source_volume": {"type": "string"},
                "backup_dir": {"type": "string"},
            },
            "required": ["source_volume", "backup_dir"],
        }
    )
    TOOLS_CACHE["mc-docker-volume-restore"] = CmdToolSpec(
        name="mc-docker-volume-restore",
        description="Restore Docker volume from tar archive",
        cmd=f"{MC_BIN_DIR}/mc-docker-volume-restore.sh",
        args=["{{target_volume}}", "{{restore_file}}"],
        input_schema={
            "type": "object",
            "properties": {
                "target_volume": {"type": "string"},
                "restore_file": {"type": "string"},
            },
            "required": ["target_volume", "restore_file"],
        }
    )
    TOOLS_CACHE["mc-traefik-start"] = CmdToolSpec(
        name="mc-traefik-start",
        description="Start Traefik proxy",
        cmd=f"{MC_BIN_DIR}/mc-traefik-start.sh",
        # args=["{{traefik_dir}}"],
        # input_schema={
        #     "type": "object",
        #     "properties": {
        #         "traefik_dir": {"type": "string"},
        #     },
        #     "required": ["traefik_dir"],
        # }
    )
    TOOLS_CACHE["mc-traefik-stop"] = CmdToolSpec(
        name="mc-traefik-stop",
        description="Stop Traefik proxy",
        cmd=f"{MC_BIN_DIR}/mc-traefik-stop.sh"
    )
    TOOLS_CACHE["mc-traefik-destroy"] = CmdToolSpec(
        name="mc-traefik-destroy",
        description="Destroy Traefik proxy",
        cmd=f"{MC_BIN_DIR}/mc-traefik-destroy.sh"
    )
    TOOLS_CACHE["mc-update-image"] = CmdToolSpec(
        name="mc-update-image",
        description="Pull latest mc docker image",
        cmd="docker",
        args=["image", "pull", "fmlabs/mc:latest"]
    )
    TOOLS_CACHE["docker-prune-buildcache"] = CmdToolSpec(
        name="docker-prune-buildcache",
        description="Prune docker build cache",
        cmd="docker",
        args=["builder", "prune", "-f"]
    )
    TOOLS_CACHE["gen-secret"] = CmdToolSpec(
        name="gen-secret",
        description="Generate a secret",
        cmd="openssl",
        args=["rand", "-hex", "{{secret_length}}"],
        input_schema={
            "type": "object",
            "properties": {
                "secret_length": {"type": "integer", "default": 32},
            },
            "required": ["secret_length"]
        }
    )
    TOOLS_CACHE["mc-ssh-node-provisioning"] = CmdToolSpec(
        name="mc-ssh-node-provisioning",
        description="Provision a new MC node",
        cmd=f"{MC_BIN_DIR}/mc-ssh-node-provisioning.sh",
        args=["{{ssh_host}}"],
        input_schema={
            "type": "object",
            "properties": {
                "ssh_host": {"type": "string"},
            },
            "required": ["ssh_host"]
        }
    )
    TOOLS_CACHE["mc-ssh-node-api-call"] = CmdToolSpec(
        name="mc-ssh-node-api-call",
        description="Call Remote API via ssh",
        cmd=f"{MC_BIN_DIR}/mc-ssh-node-api-call.sh",
        args=["{{ssh_host}}", "{{api_key}}", "{{api_path}}"],
        input_schema={
            "type": "object",
            "properties": {
                "ssh_host": {"type": "string"},
                "api_key": {"type": "string"},
                "api_path": {"type": "string", "default": "/api/health"},
            },
            "required": ["ssh_host", "api_key", "api_path"],
        }
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
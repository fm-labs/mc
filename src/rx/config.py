from __future__ import annotations

import os
import json
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional, Dict, Any

#from dotenv import load_dotenv

from rx.util import substitute_double_brace

#load_dotenv(".env.rx")

# SSH related environment variables
# generate a new key pair using:
# ssh-keygen -t rsa -b 4096 -f ~/.ssh/my-id-rsa -C "rx-ssh-key" -N "your_passphrase"
SSH_KEY_FILE = os.getenv("SSH_KEY_FILE", None) # str(Path.home().joinpath(".ssh/id_rsa")))
SSH_KEY_FILE_PASS = os.getenv("SSH_KEY_FILE_PASS", None)

# AWS related environment variables
AWS_PROFILE = os.getenv("AWS_PROFILE", None)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", None)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)


@dataclass
class Metadata:
    name: str
    version: str
    description: str

@dataclass
class BuildConfig:
    command_before: str
    command: str
    command_after: str

@dataclass
class RunConfig:
    subject: Optional[str] = None
    action: Optional[str] = None
    src: Optional[str] = None
    dest: Optional[str] = None
    command: Optional[str] = None
    # hooks
    command_before: Optional[str | list[str]] = None
    command_after: Optional[str | list[str]] = None
    # handler specific extra fields are stored in a dict
    extra: Dict[str, Any] = None

@dataclass
class Config:
    metadata: Metadata
    variables: Dict[str, Any]
    build: Dict[str, BuildConfig]  # key is target name
    run: Dict[str, RunConfig]  # key is target name

@dataclass
class GlobalContext:
    config_path: Path
    cwd: Optional[Path]
    dry_run: bool
    config: Optional[Config]



def load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("rb") as f:
        return tomllib.load(f)



def load_config(path: Path) -> Config:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as f:
        data = tomllib.load(f)

    # dump to JSON for debugging
    # todo remove
    json_path = path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    try:
        m = data["metadata"]
        metadata = Metadata(
            name=str(m.get("name", "unknown")),
            version=str(m.get("version", "0.0.0")),
            description=str(m.get("description", "")),
        )

        v = data.get("variables", data.get("vars", {}))
        v.update(m)
        #v.update(os.environ)
        variables = {}
        for k, val in v.items():
            variables[k] = substitute_double_brace(val, {})

        b = data.get("build", {})
        build_configs = {}
        for target in b:
            if isinstance(b[target], dict):
                node = b[target]
                build_configs[target] = parse_build_config(node, target, variables)

        run_configs = {}
        r = data.get("run", {})
        for target in r:
            if isinstance(r[target], dict):
                node = r[target]
                node["action"] = "run"
                run_configs[target] = parse_run_config(node, target, variables)

        r = data.get("publish", {})
        for target in r:
            if isinstance(r[target], dict):
                node = r[target]
                node["action"] = "publish"
                run_configs[target] = parse_run_config(node, target, variables)

        return Config(
            metadata=metadata,
            variables=variables,
            build=build_configs,
            run=run_configs,
        )
    except KeyError as e:
        raise ValueError(f"Missing required section/key in config: {e}")


def parse_build_config(node: dict, target: str, vars: dict) -> BuildConfig:
    command = str(node.get("command", "")).strip()
    if not command or len(command) == 0:
        raise ValueError(f"'command' field is required for build target '{target}'.")

    command_before = str(node.get("command_before", ""))
    command_after = str(node.get("command_after", ""))

    return BuildConfig(
        command_before=substitute_double_brace(command_before, vars),
        command=substitute_double_brace(command, vars),
        command_after=substitute_double_brace(command_after, vars),
    )


def parse_run_config(node: dict, target: str, vars: dict) -> RunConfig:
    subject = node.get("what", None)
    action = node.get("action", None)
    #if not action or len(action) == 0:
    #    raise ValueError(f"'action' field is required for run target '{target}'.")
    src = str(node.get("src", ""))
    #if not src or len(src) == 0:
    #    raise ValueError(f"'src' field is required for run target '{target}'.")
    dest = str(node.get("dest", ""))
    #if not dest or len(dest) == 0:
    #    raise ValueError(f"'dest' field is required for run target '{target}'.")
    command = str(node.get("command", "")).strip()
    command_before = str(node.get("command_before", ""))
    command_after = str(node.get("command_after", ""))

    # 'action' is required if 'command' is not provided
    #if len(command) > 0 and len(action) > 0:
    #    raise ValueError(f"The fields 'action' and 'command' are mutually exclusive for run target '{target}'. Provide only one of them.")
    #elif len(command) == 0 and len(action) == 0:
    #    raise ValueError(f"Either 'action' or 'command' field is required for run target '{target}'.")

    # Extract known fields and gather extra fields
    keys_of_run_config = [field.name for field in fields(RunConfig)]
    extra = {k: substitute_double_brace(v, vars) for k, v in node.items() if k not in keys_of_run_config}

    return RunConfig(
        subject=substitute_double_brace(subject, vars),
        action=substitute_double_brace(action, vars),
        src=substitute_double_brace(src, vars),
        dest=substitute_double_brace(dest, vars),
        command=substitute_double_brace(command, vars),
        # hooks
        command_before=substitute_double_brace(command_before, vars),
        command_after=substitute_double_brace(command_after, vars),
        # extra fields
        extra=extra,
    )



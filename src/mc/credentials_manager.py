"""
Manage a credentials file in YAML format.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, IO

import yaml

from mc.util.yaml_util import yaml_dump
from mc.vault import open_vaultfile


def load_credentials(path: str) -> dict:
    try:
        with open(path, "rb") as f:
            content = f.read()
        data = yaml.safe_load(content) or {}
    except Exception:
        print("[creds] Error loading data")
        raise
    if not isinstance(data, dict):
        data = {}
    return data


def dump_credentials(path: str, data: Dict[str, Any]) -> None:
    print(f"[creds] Dumping credentials...")
    try:
        with open(path, "w") as f:
            dirpath = os.path.dirname(os.path.abspath(path)) or "."
            os.makedirs(dirpath, exist_ok=True)
            yaml_dump(data, f, sort_keys=True)
    except Exception:
        print("[creds] Error writing data")
        raise


# --- Operations --------------------------------------------------------------

def add_credentials(path: str, name: str, kv: Dict[str, Any], allow_overwrite=False) -> None:
    data = load_credentials(path)
    if name in data and not allow_overwrite:
        raise RuntimeError(f"Error: credential '{name}' already exists. Use 'update' to modify it.")
    if not isinstance(kv, dict) or not kv:
        raise ValueError("Error: provide at least one key=value pair to add.")

    data[name] = kv
    dump_credentials(path, data)
    print(f"[creds] Added credential '{name}'")


def update_credentials(path: str, name: str, kv: Dict[str, Any]) -> None:
    data = load_credentials(path)
    if name not in data:
        raise RuntimeError(f"Error: credential '{name}' not found. Use 'add' to create it.")
    if not kv:
        raise ValueError("Error: provide at least one key=value pair to update.")

    # Merge/overwrite keys
    current = data.get(name, {})
    if not isinstance(current, dict):
        current = {}
    current.update(kv)
    data[name] = current
    dump_credentials(path, data)
    print(f"[creds] Updated credential '{name}'")


def remove_credentials(path: str, name: str) -> None:
    data = load_credentials(path)
    if name not in data:
        raise RuntimeError(f"Error: credential '{name}' not found.")
    del data[name]
    dump_credentials(path, data)
    print(f"[creds] Removed credential '{name}'")


def get_credentials(path: str, name: str | None) -> dict|str|None:
    data, _ = load_credentials(path)
    if name:
        return data.get(name)
    else:
        return data


@contextmanager
def credentials(vaultfile: str, vaultpassfile: str = None, mode: str = "r", encrypt: bool = True) -> Iterator[IO]:
    print("[creds] Entering credentials manager context.", encrypt, vaultfile, vaultpassfile)
    if encrypt:
        with open_vaultfile(vaultfile, mode=mode, passfile=vaultpassfile, create=True) as f: # NamedTemporaryFile
            yield f  # what becomes `f` in the with-block
    else:
        plainfile = f"{vaultfile}.yaml"
        with open(plainfile, mode) as f:
            yield f  # what becomes `f` in the with-block
    print("[creds] Exiting credentials manager context.")

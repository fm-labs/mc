"""
Manage a raw (unencrypted) vault file of credentials.
"""

from __future__ import annotations

import io
import os
import sys
import hashlib
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Tuple

import paramiko
from paramiko import RSAKey, ECDSAKey, Ed25519Key, SSHException

from mc.util.yaml_util import yaml_dump


# --- Format detection ---------------------------------------------------------

def detect_format(path: str) -> str:
    extparts = os.path.splitext(path)
    if len(extparts) == 2:
        _, ext = extparts
    else:
        ext = ""

    ext = ext.lower()
    if ext == ".toml":
        return "toml"
    if ext in (".yaml", ".yml"):
        return "yaml"
    # Default to YAML if ambiguous, per user's assumption
    return "yaml"


# --- I/O helpers for YAML / TOML ---------------------------------------------

def load_credentials(path: str) -> Tuple[Dict[str, Any], str]:
    fmt = detect_format(path)
    if not os.path.exists(path):
        # Start a new structure if file doesn't exist yet
        return {"credentials": {}}, fmt

    with open(path, "rb") as f:
        content = f.read()

    if fmt == "toml":
        # Prefer stdlib tomllib if available (Python 3.11+)
        try:
            import tomllib  # type: ignore
            data = tomllib.loads(content.decode("utf-8"))
        except ModuleNotFoundError:
            try:
                import toml  # type: ignore
            except ModuleNotFoundError:
                sys.exit("Error: Need 'tomllib' (Python 3.11+) or 'toml' package to read TOML.")
            data = toml.loads(content.decode("utf-8"))
    else:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError:
            sys.exit("Error: Need 'PyYAML' (package 'yaml') to read YAML.")
        data = yaml.safe_load(content) or {}

    if not isinstance(data, dict):
        data = {}

    # Ensure top-level key exists
    data.setdefault("credentials", {})
    if not isinstance(data["credentials"], dict):
        data["credentials"] = {}

    return data, fmt


def dump_credentials(path: str, data: Dict[str, Any], fmt: str) -> None:
    dirpath = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(dirpath, exist_ok=True)
    print(f"Writing {fmt} data to {path}...")
    #tmp = NamedTemporaryFile(mode="w+t", encoding="utf-8", delete=False)
    try:
        with open(path, "w") as f:
            if fmt == "toml":
                try:
                    import tomli_w
                    tomli_w.dump(data, f)
                except ModuleNotFoundError:
                    try:
                        import toml  # type: ignore
                    except ModuleNotFoundError:
                        raise RuntimeError("Error: Need 'tomli-w' or 'toml' package to write TOML.")
                    f.write(toml.dumps(data))
            else:
                try:
                    import yaml  # type: ignore
                except ModuleNotFoundError:
                    raise RuntimeError("Error: Need 'PyYAML' (package 'yaml') to write YAML.")
                yaml_dump(data, f, sort_keys=True)
        #os.replace(tmp.name, path)
    except Exception:
        print("Error writing data, removing temporary file.")
        #os.unlink(tmp.name)
        raise


# --- Operations --------------------------------------------------------------

def add_credentials(path: str, name: str, kv: Dict[str, Any]) -> None:
    data, fmt = load_credentials(path)
    creds = data["credentials"]

    if name in creds:
        raise RuntimeError(f"Error: credential '{name}' already exists. Use 'update' to modify it.")

    if not isinstance(kv, dict) or not kv:
        raise ValueError("Error: provide at least one key=value pair to add.")

    creds[name] = kv
    dump_credentials(path, data, fmt)
    print(f"Added credential '{name}' to {path}.")


def update_credentials(path: str, name: str, kv: Dict[str, Any]) -> None:
    data, fmt = load_credentials(path)
    creds = data["credentials"]

    if name not in creds:
        raise RuntimeError(f"Error: credential '{name}' not found. Use 'add' to create it.")

    if not kv:
        raise ValueError("Error: provide at least one key=value pair to update.")

    # Merge/overwrite keys
    current = creds.get(name, {})
    if not isinstance(current, dict):
        current = {}
    current.update(kv)
    creds[name] = current

    dump_credentials(path, data, fmt)
    print(f"Updated credential '{name}' in {path}.")


def remove_credentials(path: str, name: str) -> None:
    data, fmt = load_credentials(path)
    creds = data["credentials"]

    if name not in creds:
        raise RuntimeError(f"Error: credential '{name}' not found.")

    del creds[name]
    dump_credentials(path, data, fmt)
    print(f"Removed credential '{name}' from {path}.")


def get_credentials(path: str, name: str | None) -> dict:
    data, _ = load_credentials(path)
    creds = data.get("credentials", {})
    if name:
        entry = creds.get(name)
        if entry is None:
            raise RuntimeError(f"Error: credential '{name}' not found.")
        return entry
    else:
        return creds


def _ssh_load_key_and_fingerprint(path, password=None) -> Tuple[paramiko.PKey, str]:
    for key_class in [RSAKey, ECDSAKey, Ed25519Key]:
        try:
            key = key_class.from_private_key_file(path, password=password)
            fingerprint = ':'.join(f'{b:02x}' for b in key.get_fingerprint())
            return key, fingerprint
        except SSHException:
            continue
    raise ValueError("Unsupported or invalid key type.")


def _read_ssh_key(key_path: str = None) -> tuple[bytes, str]:

    if not key_path:
        raise ValueError("Error: SSH key path not provided.")

    if not os.path.exists(key_path):
        raise FileNotFoundError(f"SSH key file not found: {key_path}")

    with open(os.path.expanduser(key_path), "rb") as f:
        key_data = f.read()
    if not key_data:
        raise ValueError("Error: SSH key file is empty.")

    key_hash = _calculate_ssh_key_hash(key_data)
    return key_data, key_hash


def _calculate_ssh_key_hash(key_data: bytes) -> str:
    return hashlib.sha256(key_data).hexdigest()


def add_ssh_key(path: str, name: str, key_path: str, key_passphrase: str = None) -> None:
    # Try to load the key to verify it's valid and get the key fingerprint
    try:
        ssh_key, ssh_key_id = _read_ssh_key(key_path)
        pkey, fingerprint = _ssh_load_key_and_fingerprint(key_path, password=key_passphrase)
        print(f"Loaded SSH key with fingerprint: {fingerprint}")
    except Exception as e:
        raise ValueError(f"Error loading SSH key: {e}")

    creds = {"ssh_key_name": name,
             "ssh_key_id": ssh_key_id,
             "ssh_key": ssh_key,
             "ssh_key_passphrase": key_passphrase,
             "ssh_key_fingerprint": fingerprint, }
    cname = f"ssh-key-{ssh_key_id[:16]}"
    add_credentials(path, cname, creds)


    # test pkey construction with the creds
    try:
        # Decode bytes to text
        key_str = ssh_key.decode("utf-8")
        key_stream = io.StringIO(key_str)
        pkey = RSAKey.from_private_key(key_stream, password=key_passphrase)
        print(f"Test: reconstructed PKey from stored data, fingerprint: {pkey.get_fingerprint().hex()}")
    except Exception as e:
        print(f"Warning: could not reconstruct PKey from stored data: {e}")
        raise


def lookup_ssh_key_passphrase(path: str, key_path: str = None, key_id=None) -> str | None:
    if not key_path and not key_id:
        raise ValueError("Either key_path or key_id must be provided.")

    if key_path:
        _, key_id = _read_ssh_key(key_path)

    data, _ = load_credentials(path)
    creds = data.get("credentials", {})
    cname = f"ssh-key-{key_id[:16]}"
    if cname in creds:
        entry = creds[cname]
        if entry.get("ssh_key_id") != key_id:
            raise RuntimeError(f"Error: credential '{cname}' has mismatched key_id.")

        if isinstance(entry, dict):
            return entry.get("ssh_key_passphrase")

    # Fallback: search all entries for matching key_id
    for name, entry in creds.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("ssh_key_id") == key_id:
            return entry.get("ssh_key_passphrase")
    return None

import json
import os
import tempfile

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mc.config import CONFIG_DIR

router = APIRouter()

# Known config files, keyed by the `conf` query parameter.
# Write access is off by default and enabled per file with an env var set to "1".
KNOWN_CONFIGS = {
    "mc": {
        "path": os.path.join(CONFIG_DIR, "mc.conf.json"),
        "format": "json",
        "writable_env": "MC_API_CONF_MC_WRITABLE",
    },
    "ssh": {
        "path": os.path.join(CONFIG_DIR, "ssh_config"),
        "format": "text",
        "writable_env": "MC_API_CONF_SSH_WRITABLE",
    },
}


class ConfigUpdate(BaseModel):
    content: str


def _get_conf(conf: str) -> dict:
    if conf not in KNOWN_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown config: {conf}")
    return KNOWN_CONFIGS[conf]


def _is_writable(entry: dict) -> bool:
    # Read the real process env, not mc.conf.json's "environment" block,
    # so editing mc.conf.json can't grant itself (or ssh_config) write access.
    return os.getenv(entry["writable_env"], "") == "1"


def _describe(conf: str, entry: dict) -> dict:
    path = entry["path"]
    exists = os.path.isfile(path)
    content = ""
    if exists:
        with open(path) as f:
            content = f.read()
    return {
        "conf": conf,
        "path": path,
        "format": entry["format"],
        "exists": exists,
        "writable": _is_writable(entry),
        "content": content,
    }


@router.get("/config")
def get_config(conf: str = Query(...)):
    return _describe(conf, _get_conf(conf))


@router.post("/config")
def update_config(body: ConfigUpdate, conf: str = Query(...)):
    entry = _get_conf(conf)
    if not _is_writable(entry):
        raise HTTPException(
            status_code=403,
            detail=f"Config '{conf}' is read-only. Set {entry['writable_env']}=1 to allow edits.",
        )

    if entry["format"] == "json":
        try:
            json.loads(body.content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}") from e

    # Write atomically: temp file in the same dir, then rename over the original.
    path = entry["path"]
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    mode = os.stat(path).st_mode & 0o777 if os.path.exists(path) else 0o600
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body.content)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return _describe(conf, entry)

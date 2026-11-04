import json
import os
import secrets
import re
from pathlib import Path

from dotenv import load_dotenv

from mc.util.pkg_util import get_pkg_version

# Zero-config settings
API_NAME = "mission-control"
API_VERSION = get_pkg_version("mc")
API_PREFIX = "/api"

load_dotenv(".env")
load_dotenv(".env.local")

MC_DEV_MODE = os.getenv("MC_DEV_MODE", "false").lower() == "true"
MC_HOME = str(Path(os.getenv("MC_HOME", "/mc")).resolve())
MC_CONFIG_DIR = str(Path(os.getenv("MC_CONFIG_DIR", f"{MC_HOME}/etc")).resolve())
MC_BIN_DIR = str(Path(os.getenv("MC_BIN_DIR", "./scripts")).resolve())
MC_BACKUP_DIR = os.getenv("MC_BACKUP_DIR", "/tmp/backup") # in docker environments, this is on the host!

# the real path to MC_HOME on a docker host
DOCKER_HOME = os.getenv("DOCKER_HOME", "/var/lib/docker")

MC_DATA_VOLUME = os.getenv("MC_DATA_VOLUME", "mc_data")
MC_HOST_HOME = os.getenv("MC_HOST_HOME", os.path.join(DOCKER_HOME, "volumes", MC_DATA_VOLUME, "_data"))

def get_mc_real_path(mc_path: str | Path) -> Path:
    # replace MC_HOME with MC_HOST_HOME
    # paths outside MC_HOME get rejected
    mc_path = Path(mc_path).resolve()
    if not str(mc_path).startswith(MC_HOME):
        raise ValueError(f"Path {mc_path} is outside of MC_HOME {MC_HOME}")
    return Path(str(mc_path).replace(MC_HOME, MC_HOST_HOME, 1))

_VARS_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

def _expand(value: str, vars: dict[str, str], missing: set[str]) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in vars:
            missing.add(name)
            return match.group(0)
        return str(vars[name])
    return _VARS_PLACEHOLDER.sub(replace, value)


def expand_dict_vars(source: dict[str, str], vars: dict[str, str]) -> dict[str, str]:
    """
    Replace all placeholders in dict values with params. Placeholders use '{{var_name}}' pattern.
    :raises KeyError: if a placeholder has no matching param
    """
    missing: set[str] = set()
    result = {key: _expand(value, vars, missing) for key, value in source.items()}
    if missing:
        raise KeyError(f"Missing params for placeholders: {', '.join(sorted(missing))}")
    return result


def expand_list_vars(source: list[str], vars: dict[str, str]) -> list[str]:
    """
    Replace all placeholders in list items with vars. Placeholders use '{{var_name}}' pattern.
    :raises KeyError: if a placeholder has no matching var
    """
    missing: set[str] = set()
    result = [_expand(item, vars, missing) for item in source]
    if missing:
        raise KeyError(f"Missing params for placeholders: {', '.join(sorted(missing))}")
    return result


def read_config(filepath: str) -> dict:
    if os.path.exists(filepath):
        print(f"Loading config from {filepath}")
        try:
            with open(filepath) as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Error reading mc.json: {e}")
    return {}


def write_config(config: dict, filepath: str):
    try:
        with open(filepath, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error writing mc.json: {e}")


def merge_deep(config: dict, config2: dict) -> dict:
    for k, v in config.items():
        if k in config2:
            config[k] = merge_deep(v, config2[k])
        else:
            config[k] = v
    for k, v in config2.items():
        if k not in config:
            config[k] = v
    return config


def load_config():
    config_dirs = [
        "/etc/mc",
        os.path.join(MC_HOME, "etc"),
    ]
    merged_config = {}
    for d in config_dirs:
        filepath = os.path.join(d, "mc.conf.json")
        if os.path.exists(filepath):
            conf = read_config(filepath)
            if conf:
                merged_config = merge_deep(merged_config, conf)
    return merged_config

CONFIG = load_config()

def env_var(name: str, default=None) -> str | None:
    global CONFIG
    if "environment" in CONFIG and name in CONFIG["environment"]:
        return CONFIG["environment"][name]

    value = os.getenv(name, default)
    if value is None:
        print(f"Warning: Environment variable {name} is not set and no default value provided.")
    return value

def env_var_bool(name: str, default: bool = False) -> bool:
    val = env_var(name, None)
    if val is None:
        return default
    return val.lower() == "true" or val == "1"

def generate_random_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def get_node_proxy_config(node_name: str) -> tuple[str, str] | None:
    """Get node proxy config from docker hosts config"""
    node = CONFIG.get("docker_hosts", {}).get(node_name)
    if node and node.get("url", "").startswith("node+http"):
        base_url = node.get("url")[len("node+"):].rstrip("/")
        api_key = node.get("api_key")
        return base_url, api_key
    return None


# Additional paths

# Inventory storage: directory (one JSON file per item), file (one JSON file per type) or sqlite
INVENTORY_STORAGE = env_var("INVENTORY_STORAGE", "directory")
# Inventory: load the Python modules of user item types in $MC_CONFIG_DIR/inventory (schema-only types always load)
INVENTORY_USER_CODE = env_var("INVENTORY_USER_CODE", "false").lower() == "true"
# SSH_CONFIG = get_env_var("SSH_CONFIG", f"{MC_HOME}/etc/ssh_config")
# HOST_DATA_DIR = get_env_var("HOST_DATA_DIR", "/mc") # deprecated
# HOST_MC_CONFIG_DIR = get_env_var("HOST_MC_CONFIG_DIR", "/mc/etc") # deprecated

# Admin credentials
USERS_FILE = f"{MC_CONFIG_DIR}/users.json"

# Api Key auth
MC_API_KEY = env_var("MC_API_KEY", None)

# Mongodb connection settings
MONGODB_URL = env_var("MONGODB_URL", "")

# Redis connection settings
# REDIS_URL is preferred if set
REDIS_URL = env_var("REDIS_URL", "")
# or
REDIS_HOST = env_var("REDIS_HOST", "")
REDIS_PORT = int(env_var("REDIS_PORT", "6379"))
REDIS_DB = int(env_var("REDIS_DB", "0"))
REDIS_PASSWORD = env_var("REDIS_PASSWORD", "")

# Vault settings
VAULT_ENABLED = env_var("VAULT_ENABLED", "false").lower() == "true"
VAULT_FILE = env_var("VAULT_FILE", f"{MC_CONFIG_DIR}/credentials.vault")
VAULT_PASS_FILE = env_var("VAULT_PASS_FILE", f"{MC_CONFIG_DIR}/credentials.vault.pass")

# JWT settings
JWT_ISSUER = "mc"
JWT_AUDIENCE = "mc"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 60 minutes
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
JWT_ALGORITHM = "HS256"
# should be kept secret:
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", default=generate_random_secret(32))
JWT_REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET_KEY", default=generate_random_secret(32))

# CORS
MC_CORS_ENABLED = env_var_bool("MC_CORS_ENABLED", True)
MC_CORS_ALLOWED_ORIGINS = env_var("MC_CORS_ALLOWED_ORIGINS", "*")

# MCP
MC_MCP_ENABLED = env_var_bool("MC_MCP_ENABLED", True)
MC_MCP_TOKEN = env_var("MC_MCP_TOKEN", default=generate_random_secret(32))

# NODE PROXY
MC_NODE_PROXY_ENABLED = env_var_bool("MC_NODE_PROXY_ENABLED", False)

# Github personal access token
# GITHUB_TOKEN = get_env_var("GITHUB_TOKEN", "")

# Github OAuth settings
# GITHUB_CLIENT_ID = get_env_var("GITHUB_CLIENT_ID")
# GITHUB_CLIENT_SECRET = get_env_var("GITHUB_CLIENT_SECRET")
# GITHUB_CALLBACK_URL = get_env_var("GITHUB_CALLBACK_URL")



# def set_dotenv_var(key: str, value: str):
#     env_path = os.getenv("MC_ENV", f"{MC_HOME}/.env.local")
#     lines = []
#     if os.path.exists(env_path):
#         with open(env_path) as f:
#             lines = f.readlines()
#     with open(env_path, "w") as f:
#         found = False
#         for line in lines:
#             if line.startswith(f"{key}="):
#                 f.write(f"{key}={value}\n")
#                 found = True
#             else:
#                 f.write(line)
#         if not found:
#             f.write(f"{key}={value}\n")
#
#
# def set_env_var(name: str, value: str):
#     os.environ[name] = value
#     set_dotenv_var(name, value)


# def write_dotenv(config: dict):
#     env_path = os.getenv("MC_ENV", f"{MC_HOME}/.env.development")
#     try:
#         with open(env_path, "w") as f:
#             for key, value in config.items():
#                 f.write(f"{key}={value}\n")
#     except Exception as e:
#         print(f"Error writing .env file: {e}")

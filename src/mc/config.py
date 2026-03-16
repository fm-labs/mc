import os
import json

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local")

# Paths
DATA_DIR = os.getenv("DATA_DIR", "/opt/mc")

load_dotenv(f"{DATA_DIR}/.env")
load_dotenv(f"{DATA_DIR}/.env.local")

def read_config():
    configs_path = os.getenv("MC_CONFIG", f"{DATA_DIR}/mc.json")
    if os.path.exists(configs_path):
        print(f"Loading config from {configs_path}")
        try:
            with open(configs_path, "r") as f:
                configs = json.load(f)
                return configs
        except Exception as e:
            print(f"Error reading mc.json: {e}")
    return None

CONFIG = read_config() or {}

def get_env_var(name: str, default=None):
    if name in CONFIG:
        return CONFIG[name]

    value = os.getenv(name, default)
    if value is None:
        print(f"Warning: Environment variable {name} is not set and no default value provided.")
    return value


# Additional paths
CONFIG_DIR = get_env_var("CONFIG_DIR", f"{DATA_DIR}/etc")
RESOURCES_DIR = get_env_var("RESOURCES_DIR", f"{DATA_DIR}/resources")
#SSH_CONFIG = get_env_var("SSH_CONFIG", f"{DATA_DIR}/etc/ssh_config")
#HOST_DATA_DIR = get_env_var("HOST_DATA_DIR", "/opt/mc") # deprecated
#HOST_CONFIG_DIR = get_env_var("HOST_CONFIG_DIR", "/opt/mc/etc") # deprecated

# Admin credentials
USERS_FILE = f"{CONFIG_DIR}/users.json"

# Mongodb connection settings
MONGODB_URL = get_env_var("MONGODB_URL", "")

# Redis connection settings
# REDIS_URL is preferred if set
REDIS_URL = get_env_var("REDIS_URL", "")
# or
REDIS_HOST = get_env_var("REDIS_HOST", "")
REDIS_PORT = int(get_env_var("REDIS_PORT", "6379"))
REDIS_DB = int(get_env_var("REDIS_DB", "0"))
REDIS_PASSWORD = get_env_var("REDIS_PASSWORD", "")

# Vault settings
VAULT_ENABLED = get_env_var("VAULT_ENABLED", "false").lower() == "true"
VAULT_FILE = get_env_var("VAULT_FILE", f"{CONFIG_DIR}/credentials.vault")
VAULT_PASS_FILE = get_env_var("VAULT_PASS_FILE", f"{CONFIG_DIR}/credentials.vault.pass")

# Github personal access token
# GITHUB_TOKEN = get_env_var("GITHUB_TOKEN", "")

# Github OAuth settings
# GITHUB_CLIENT_ID = get_env_var("GITHUB_CLIENT_ID")
# GITHUB_CLIENT_SECRET = get_env_var("GITHUB_CLIENT_SECRET")
# GITHUB_CALLBACK_URL = get_env_var("GITHUB_CALLBACK_URL")



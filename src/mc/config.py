import os
import json

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local")

# Paths
DATA_DIR = os.getenv("DATA_DIR", "/opt/mc")
CONFIG_DIR = os.getenv("CONFIG_DIR", f"{DATA_DIR}/etc")
RESOURCES_DIR = os.getenv("RESOURCES_DIR", f"{DATA_DIR}/resources")
#SSH_CONFIG = os.getenv("SSH_CONFIG", f"{DATA_DIR}/etc/ssh_config")
#HOST_DATA_DIR = os.getenv("HOST_DATA_DIR", "/opt/mc") # deprecated
#HOST_CONFIG_DIR = os.getenv("HOST_CONFIG_DIR", "/opt/mc/etc") # deprecated

def read_config():
    configs_path = os.getenv("SETTINGS_JSON_PATH", f"{DATA_DIR}/mc.json")
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


# Admin credentials
MC_ADMIN_EMAIL = get_env_var("MC_ADMIN_EMAIL", "johndoe@example.org")
MC_ADMIN_PASSWORD = get_env_var("MC_ADMIN_PASSWORD", "secret")
if get_env_var("MC_ADMIN_PASSWORD_FILE"):
    with open(get_env_var("MC_ADMIN_PASSWORD_FILE"), "r") as f:
        MC_ADMIN_PASSWORD = f.read().strip()

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



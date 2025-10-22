import json
import os

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv(".env")

DATA_DIR = os.getenv("DATA_DIR", os.getcwd() + "/data")
CONFIG_DIR = os.getenv("CONFIG_DIR", os.getcwd() + "/config")
RESOURCES_DIR = os.environ.get("RESOURCES_DIR", os.getcwd() + "/resources")
#TMP_DIR = os.environ.get("TMP_DIR", default=None) # None = use system temp dir
TMP_DIR = os.path.join(DATA_DIR, "tmp")

PLUGINS_ENABLED = ["tools", "xscan", "orchestra", "cloudscan", "demo", "containers", "aws"]

INTEGRATIONS_ENABLED = ["github", "dockerhub", "docker"]

HOST_DATA_DIR = os.getenv("HOST_DATA_DIR")
HOST_CONFIG_DIR = os.getenv("HOST_CONFIG_DIR")

MONGODB_URL = os.getenv("MONGODB_URL", "")

# redis connection settings
# REDIS_URL is preferred if set
REDIS_URL = os.getenv("REDIS_URL", "")
# or
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

VAULT_FILE = os.getenv("VAULT_FILE", f"{CONFIG_DIR}/credentials.yml")
VAULT_PASS_FILE = os.getenv("VAULT_PASS_FILE", f"{CONFIG_DIR}/credentials.password.txt")


def load_config_json(file_name: str) -> dict|list:
    file_path = f"{CONFIG_DIR}/{file_name}.json"
    with open(file_path, 'r') as f:
        return json.load(f)

def save_config_json(file_name: str, data: dict|list) -> None:
    file_path = f"{CONFIG_DIR}/{file_name}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def get_plugin_data_dir(plugin_name: str, makedirs=True) -> str:
    """
    Returns the data directory path for a given plugin.
    """
    path = f"{DATA_DIR}/plugins/{plugin_name}"
    if makedirs:
        os.makedirs(path, exist_ok=True)
    return path

def get_plugin_config_dir(plugin_name: str, makedirs=True) -> str:
    """
    Returns the config directory path for a given plugin.
    """
    path = f"{CONFIG_DIR}/plugins/{plugin_name}"
    if makedirs:
        os.makedirs(path, exist_ok=True)
    return path

def get_plugin_host_data_dir(plugin_name: str) -> str:
    """
    Returns the host data directory path for a given plugin.
    In a Docker-in-Docker setup, this path is mapped to the container.
    """
    if not HOST_DATA_DIR:
        raise ValueError("HOST_DATA_DIR is not set in environment variables.")
    path = f"{HOST_DATA_DIR}/plugins/{plugin_name}"
    return path

def get_plugin_host_config_dir(plugin_name: str) -> str:
    """
    Returns the host config directory path for a given plugin.
    In a Docker-in-Docker setup, this path is mapped to the container.
    """
    if not HOST_CONFIG_DIR:
        raise ValueError("HOST_CONFIG_DIR is not set in environment variables.")
    path = f"{HOST_CONFIG_DIR}/plugins/{plugin_name}"
    return path


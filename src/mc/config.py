import os

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local")

# Enabled plugins and integrations
PLUGINS_ENABLED = ["tools", "xscan", "orchestra", "cloudscan", "demo", "containers", "aws", "mcpman", "paypal"]
INTEGRATIONS_ENABLED = ["github", "dockerhub", "docker"]

# Paths
SSH_CONFIG = os.getenv("SSH_CONFIG", os.getcwd() + "/config/ssh_config")
DATA_DIR = os.getenv("DATA_DIR", os.getcwd() + "/data")
CONFIG_DIR = os.getenv("CONFIG_DIR", os.getcwd() + "/config")
RESOURCES_DIR = os.environ.get("RESOURCES_DIR", os.getcwd() + "/resources")
HOST_DATA_DIR = os.getenv("HOST_DATA_DIR") # deprecated
HOST_CONFIG_DIR = os.getenv("HOST_CONFIG_DIR") # deprecated

# Mongodb connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "")

# Redis connection settings
# REDIS_URL is preferred if set
REDIS_URL = os.getenv("REDIS_URL", "")
# or
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Vault settings
VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() == "true"
VAULT_FILE = os.getenv("VAULT_FILE", f"{CONFIG_DIR}/credentials.vault")
VAULT_PASS_FILE = os.getenv("VAULT_PASS_FILE", f"{CONFIG_DIR}/credentials.vault.pass")

# Github personal access token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Github OAuth settings
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"


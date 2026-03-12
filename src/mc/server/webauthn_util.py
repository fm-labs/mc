import base64
import json
from pathlib import Path

from mc.config import DATA_DIR

# In-memory stores for challenges and users
CHALLENGES: dict[str, bytes] = {}  # e.g., keyed by username
USERS: dict[str, dict] = {}

#CREDENTIALS: dict[str, list[dict]] = {}
CREDENTIALS_STORE_DIR = f"{DATA_DIR}/webauthn_credentials"
Path(CREDENTIALS_STORE_DIR).mkdir(parents=True, exist_ok=True)


def webauthn_store_challenge(username: str, challenge: bytes):
    global CHALLENGES
    CHALLENGES[username] = challenge

def webauthn_get_challenge(username: str) -> bytes | None:
    global CHALLENGES
    return CHALLENGES.get(username)

def webauthn_remove_challenge(username: str):
    global CHALLENGES
    if username in CHALLENGES:
        del CHALLENGES[username]

def webauthn_add_user(username: str, user_info: dict):
    global USERS
    USERS[username] = user_info

def webauthn_get_user(username: str) -> dict | None:
    global USERS
    return USERS.get(username)


def webauthn_add_credential(username: str, credential: dict):
    # Store credentials in a file per user
    user_cred_file = f"{CREDENTIALS_STORE_DIR}/{username}_creds.json"
    creds = []
    if Path(user_cred_file).exists():
        with open(user_cred_file, "r") as f:
            creds = json.load(f)
    creds.append(credential)
    with open(user_cred_file, "w") as f:
        json.dump(creds, f)

def webauthn_get_credentials(username: str) -> list[dict]:
    # Retrieve credentials from file per user
    user_cred_file = f"{CREDENTIALS_STORE_DIR}/{username}_creds.json"
    if Path(user_cred_file).exists():
        with open(user_cred_file, "r") as f:
            creds = json.load(f)
        return creds
    return []

# def b64_encode(data: bytes) -> str:
#     return base64.b64encode(data).decode("ascii")
#
# def b64_decode(data: str) -> bytes:
#     return base64.b64decode(data)
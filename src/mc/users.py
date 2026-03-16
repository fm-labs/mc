import dataclasses
import os

import bcrypt

from mc.config import USERS_FILE

@dataclasses.dataclass
class User:
    username: str
    hashed_password: str


def _load(path: str) -> dict[str, str]:
    users = {}
    if not os.path.exists(path):
        return users
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and ":" in line:
                user, hashed = line.split(":", 1)
                users[user] = hashed
    return users


def _save(path: str, users: dict[str, str]) -> None:
    with open(path, "w") as f:
        for user, hashed in sorted(users.items()):
            f.write(f"{user}:{hashed}\n")


def create_user_file(path: str = USERS_FILE) -> None:
    """Create an empty passwd file (no-op if it already exists)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w"):
            pass
        print(f"Created {path}")
    else:
        print(f"{path} already exists — skipping")


def add_user(username: str, password: str,
             path: str = USERS_FILE) -> None:
    """Add a new user. Raises ValueError if the user already exists."""
    users = _load(path)
    if username in users:
        raise ValueError(f"User '{username}' already exists")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = hashed
    _save(path, users)
    print(f"Added user '{username}'")


def get_user(username: str, path: str = USERS_FILE) -> dict[str, str]:
    """Return user info dict with 'username' and 'hashed_password'. Raises KeyError if not found."""
    users = _load(path)
    if username not in users:
        raise KeyError(f"User '{username}' not found")
    return {"username": username, "hashed_password": users[username]}


def remove_user(username: str, path: str = USERS_FILE) -> None:
    """Remove a user. Raises KeyError if the user does not exist."""
    users = _load(path)
    if username not in users:
        raise KeyError(f"User '{username}' not found")
    del users[username]
    _save(path, users)
    print(f"Removed user '{username}'")


def authenticate_user(username: str, password: str,
                      path: str = USERS_FILE) -> User|None:
    """Return True if username exists and password matches."""
    try:
        user = get_user(username, path)
    except KeyError:
        return None
    if bcrypt.checkpw(password.encode(), user["hashed_password"].encode()):
        return User(username=username, hashed_password=user["hashed_password"])
    return None


def change_password(username: str, old_password: str, new_password: str):
    """Change a user's password. Raises KeyError if user not found, ValueError if old password is incorrect."""
    users = _load(USERS_FILE)
    if username not in users:
        raise KeyError(f"User '{username}' not found")
    if not bcrypt.checkpw(old_password.encode(), users[username].encode()):
        raise ValueError("Old password is incorrect")
    new_hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    users[username] = new_hashed
    _save(USERS_FILE, users)
    print(f"Password for user '{username}' has been changed")


def set_password(username: str, new_password: str):
    """Set a user's password without checking the old one. Raises KeyError if user not found."""
    users = _load(USERS_FILE)
    if username not in users:
        raise KeyError(f"User '{username}' not found")
    new_hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    users[username] = new_hashed
    _save(USERS_FILE, users)
    print(f"Password for user '{username}' has been set")

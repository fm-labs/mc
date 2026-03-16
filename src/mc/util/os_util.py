from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List


def lookup_bin_path(bin_name: str) -> str | None:
    """
    Check if a binary is installed and return its path, or None if not found.
    If the bin_name is an absolute path, check if it exists.
    Fallback to target variable if provided.
    """
    if bin_name.startswith("/"):
        return bin_name if Path(bin_name).exists() else None

    # Check for environment variable override
    # e.g. CURL_BIN=/usr/local/bin/curl
    env_var = f"{bin_name.upper()}_BIN"
    if env_var in os.environ and len(str(os.environ[env_var]).strip()) > 0:
        return os.environ[env_var]

    return shutil.which(bin_name) or None


def bin_cmd(bin_name: str, args: List[str]) -> List[str]:
    bin_path = lookup_bin_path(bin_name)
    if not bin_path:
        raise EnvironmentError(f"Required binary '{bin_name}' is not installed or not found in PATH.")
    return [bin_path] + args

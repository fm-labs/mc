import json
import os
import logging

from mc.config import DATA_DIR

logger = logging.getLogger(__name__)

# Placeholder vault implementation using a JSON file to store secrets.
# todo enable encryption
VAULT_FILE = f"{DATA_DIR}/etc/secrets.json"


def vault_set_value(item_id: str, value: str):
    """
    Set the value of a secret in the vault file.
    """
    logger.warning(f"Setting secret value in vault: id={item_id}, value={len(value)} characters")
    vault_data = _read_vault_file()
    vault_data[item_id] = value
    _write_vault_file(vault_data)


def vault_get_value(item_id: str) -> str | None:
    """
    Get the value of a secret from the vault file.
    """
    logger.warning(f"Getting secret value from vault: id={item_id}")
    vault_data = _read_vault_file()
    value = vault_data.get(item_id)
    if value is not None:
        logger.warning(f"Secret value found in vault: id={item_id}, value={len(value)} characters")
    else:
        logger.warning(f"Secret value not found in vault: id={item_id}")
    return value


def _read_vault_file() -> dict:
    """
    Read the vault file and return a dictionary of secrets.
    """
    if not os.path.exists(VAULT_FILE):
        logger.warning("Vault file does not exist, returning empty vault.")
        return {}
    with open(VAULT_FILE, "r") as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            logger.error("Error decoding vault file, returning empty vault.")
            return {}


def _write_vault_file(data: dict):
    """
    Write the given data to the vault file.
    """
    with open(VAULT_FILE, "w") as f:
        json.dump(data, f, indent=4)
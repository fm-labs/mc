from pathlib import Path
import json

from mc.config import INTEGRATIONS_ENABLED, CONFIG_DIR
from mc.integrations import INTEGRATIONS


def get_enabled_integrations() -> list:
    """
    Return a list of enabled integrations.
    """
    enabled = INTEGRATIONS_ENABLED # list of str
    available_integrations = INTEGRATIONS # list of integration definitions
    return [integration for integration in available_integrations if integration['name'] in enabled]


def is_integration_enabled(integration_name: str) -> bool:
    """
    Check if an integration is enabled.
    """
    return integration_name in INTEGRATIONS_ENABLED


def is_integration_connected_for_user(integration_name: str, user_id: str) -> bool:
    """
    Check if an integration is connected for a given user.
    """
    if not is_integration_enabled(integration_name):
        return False

    config = get_integration_config(integration_name, user_id)
    if config is None:
        return False

    if isinstance(config, list) and len(config) > 0:
        return True

    return False


def get_integration_config(integration_name: str, user_id: str) -> dict | None:
    """
    Get the configuration for a given integration and user.
    """
    config_dir = Path(CONFIG_DIR) / "integrations"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = config_dir / f"config_{integration_name}_{user_id}.json"
    if config_file_path.exists():
        with open(config_file_path, 'r') as f:
            return json.load(f)
    return None


def save_integration_config(integration_name: str, user_id: str, config: dict) -> Path:
    """
    Save the configuration for a given integration and user.
    """
    config_dir = Path(CONFIG_DIR) / "integrations"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = config_dir / f"config_{integration_name}_{user_id}.json"
    with open(config_file_path, 'w') as f:
        json.dump(config, f, indent=4)
    return config_file_path


def handle_integration_event(event_type: str, integration_name: str, user_id: str, data: dict) -> dict:
    """
    Handle an integration event.
    """
    # This is a placeholder for handling integration events.
    # In a real implementation, this could involve logging the event,
    # sending notifications, updating a database, etc.
    print(f"Event: {event_type}, Integration: {integration_name}, User: {user_id}, Details: {data}")
    return {"status": "unknown", "integration": integration_name}
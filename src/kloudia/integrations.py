from kloudia.config import load_config_json


def load_integration_properties(integration_type: str, plugin_id: str) -> dict | None:
    # get github credentials from integration settings
    integrations = load_config_json("integrations")
    integration = None
    for integration in integrations:
        if integration["integration_type"] == integration_type and integration["plugin_id"] == plugin_id:
            integration = integration
            break
    if not integration or "properties" not in integration:
        return None

    return integration["properties"]
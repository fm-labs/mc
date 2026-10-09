from mc.vault2 import vault_set_value


def handle_secrets_set_value(item: dict, action_params: dict) -> dict:
    item_id = item.get("id")
    scope = item.get("scope", "global")
    label = item.get("label")
    provider = item.get("provider")
    if not item_id:
        raise ValueError("Missing secret id")
    if not label:
        raise ValueError("Missing secret label")
    if provider not in ["vault"]:
        raise ValueError("Unsupported secret provider: {provider}")

    print(f"Setting secret '{label}' of provider '{provider}' in scope '{scope}' ...")
    vault_set_value(item_id, action_params.get("value"))
    return {
        "status": "success",
        "message": f"Variable '{label}' of provider '{provider}' set successfully in scope '{scope}'.",
    }


actions = {
    "set_value": handle_secrets_set_value,
}

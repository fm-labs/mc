import os

from mc import config
from mc.credentials import add_ssh_key, remove_ssh_key
from mc.inventory.storage import get_inventory_storage_instance


def handle_credential_configure(item: dict, action_params: dict) -> dict:
    props = item.get("properties", {})

    key_name = props.get("ssh_key_name", item['name'])
    key_path = f"~/.ssh/{key_name}"

    pkey_str = action_params.get("pkey", "")
    pkey_passphrase = action_params.get("pkey_passphrase", "")
    pkey_overwrite = action_params.get("overwrite", False)

    print("Pkey string length:", len(pkey_str))
    print("Overwrite flag:", pkey_overwrite)

    # Write the private key to the specified path
    expanded_key_path = os.path.expanduser(key_path)
    os.makedirs(os.path.dirname(expanded_key_path), exist_ok=True)
    if os.path.exists(expanded_key_path) and not pkey_overwrite:
        raise FileExistsError(f"SSH key file already exists: {expanded_key_path}")

    with open(expanded_key_path, "w") as f:
        f.write(pkey_str)
    os.chmod(expanded_key_path, 0o600)
    print(f"Wrote SSH private key to {expanded_key_path}")

    creds_file = config.VAULT_FILE + ".yaml"
    add_ssh_key(str(creds_file), key_name, expanded_key_path, key_passphrase=pkey_passphrase)

    #with open_vaultfile(config.VAULT_FILE, passfile=config.VAULT_PASS_FILE, mode="w", create=True) as vault_file:
    #    add_ssh_key(str(vault_file), key_name, expanded_key_path, key_passphrase=pkey_passphrase)

    return {"message": f"Credential '{item['name']}' configured with SSH key '{key_name}'."}


def handle_credential_destroy(item: dict, action_params: dict) -> dict:
    props = item.get("properties", {})

    key_name = props.get("ssh_key_name", item['name'])
    key_path = f"~/.ssh/{key_name}"

    expanded_key_path = os.path.expanduser(key_path)
    if os.path.exists(expanded_key_path):
        os.remove(expanded_key_path)
        print(f"Removed SSH private key file: {expanded_key_path}")
    else:
        print(f"SSH private key file not found, skipping removal: {expanded_key_path}")

    creds_file = config.VAULT_FILE + ".yaml"
    # Remove the credential from the credentials file
    try:
        remove_ssh_key(str(creds_file), key_name, expanded_key_path)
        print(f"Removed credential '{key_name}' from credentials file.")
    except Exception as e:
        print(f"Failed to remove credential '{key_name}': {e}")

    storage = get_inventory_storage_instance()
    storage.delete_item("credential", item['item_key'])

    return {"message": f"Credential '{item['name']}' destroyed."}


actions = {
    "configure": handle_credential_configure,
    "destroy": handle_credential_destroy,
}
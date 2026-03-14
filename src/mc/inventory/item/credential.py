import tempfile

from mc import config
from mc.credentials_manager import credentials
from mc.sshkey_manager import add_ssh_key

def handle_credential_configure(item: dict, action_params: dict) -> dict:
    key_name = item['name']

    pkey_str = action_params.get("pkey", "")
    pkey_passphrase = action_params.get("pkey_passphrase", "")
    pkey_overwrite = action_params.get("overwrite", False)
    print("Pkey string length:", len(pkey_str))
    print("Overwrite flag:", pkey_overwrite)

    # Write the private key to the specified path
    #key_path = f"~/.ssh/{key_name}"
    #expanded_key_path = os.path.expanduser(key_path)
    #os.makedirs(os.path.dirname(expanded_key_path), exist_ok=True)
    #if os.path.exists(expanded_key_path) and not pkey_overwrite:
    #    raise FileExistsError(f"SSH key file already exists: {expanded_key_path}")

    expanded_key_path = tempfile.NamedTemporaryFile()
    with open(str(expanded_key_path), "w") as f:
       f.write(pkey_str)
    #os.chmod(expanded_key_path, 0o600)
    #print(f"Wrote SSH private key to {expanded_key_path}")

    vaultfile = config.VAULT_FILE
    vaultpassfile = config.VAULT_PASS_FILE
    with credentials(mode="w", vaultfile=vaultfile, vaultpassfile=vaultpassfile, encrypt=True) as f:
        add_ssh_key(f.name, key_name,
                    key_file=str(expanded_key_path), key_passphrase=pkey_passphrase, allow_overwrite=pkey_overwrite)
    return {"message": f"Credential '{item['name']}' configured with SSH key '{key_name}'."}


def handle_credential_destroy(item: dict, action_params: dict) -> dict:
    # props = item
    # key_name = props.get("ssh_key_name", item['name'])
    # key_path = f"~/.ssh/{key_name}"
    # expanded_key_path = os.path.expanduser(key_path)
    # if os.path.exists(expanded_key_path):
    #     os.remove(expanded_key_path)
    #     print(f"Removed SSH private key file: {expanded_key_path}")
    # else:
    #     print(f"SSH private key file not found, skipping removal: {expanded_key_path}")
    #
    # creds_file = config.VAULT_FILE + ".yaml"
    # # Remove the credential from the credentials file
    # try:
    #     remove_ssh_key(str(creds_file), key_name, expanded_key_path)
    #     print(f"Removed credential '{key_name}' from credentials file.")
    # except Exception as e:
    #     print(f"Failed to remove credential '{key_name}': {e}")
    #
    # storage = get_inventory_storage_instance()
    # storage.delete_item("credential", item['id'])
    # return {"message": f"Credential '{item['name']}' destroyed."}
    return {"message": f"Not implemented."}



actions = {
    "configure": handle_credential_configure,
    "destroy": handle_credential_destroy,
}
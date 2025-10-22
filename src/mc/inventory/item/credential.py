import os
import subprocess

from mc import config
from mc.credentials import add_ssh_key
from xvault.vault import open_vaultfile


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



actions = {
    "configure": handle_credential_configure,
}
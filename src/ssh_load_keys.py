import os

from mc import config
from mc.credentials_manager import get_credentials
from mc.util.ssh_agent_util import ssh_agent_start, ssh_agent_is_running, ssh_agent_list_keys, \
    build_ssh_pkey_from_buffer, pkey_to_openssh_publine, ssh_agent_add_key_file
from ssh_configure import dump_ssh_and_ansible_config
from mc.vault import open_vaultfile

encrypted_vault_file = config.VAULT_FILE
password_file = config.VAULT_PASS_FILE
decrypted_creds_file = f"{encrypted_vault_file}.yaml"


def ssh_agent_load_keys_from_vault(vaultfile: str, password_file: str) -> None:
    with open_vaultfile(vaultfile, passfile=password_file, mode="r") as vault_file:
        ssh_agent_load_keys_from_credentials_file(str(vault_file.name))


def ssh_agent_load_keys_from_credentials_file(creds_file: str) -> None:
    creds = get_credentials(creds_file, None)
    # iterate creds, find creds with "ssh_key_id" field
    for cname, cdata in creds.items():
        if "ssh_key_id" in cdata:
            key_id = cdata["ssh_key_id"]
            key_name = cdata["ssh_key_name"]
            print(f">>> Found ssh credential {cname} with key_id {key_id}")
            key_data = cdata.get("ssh_key")  # bytes
            passphrase = cdata.get("ssh_key_passphrase")
            if passphrase is not None:
                if passphrase == "null" or passphrase == "":
                    passphrase = None

            if not key_data:
                print(f"Skipping {cname}, no key data found")
                continue

            try:
                pkey = build_ssh_pkey_from_buffer(key_data, passphrase)
                print(f"Pkey loaded. type: {type(pkey)}, fingerprint: {pkey.get_fingerprint().hex()}")
                pubkey = pkey_to_openssh_publine(pkey, comment=cname)
                print(f"Public key: {pubkey}")

                key_file_path = os.path.expanduser(f"~/.ssh/{key_name}")
                os.makedirs(os.path.dirname(key_file_path), exist_ok=True)
                if not os.path.exists(key_file_path):
                    with open(key_file_path, "wb") as kf:
                        kf.write(key_data)
                    os.chmod(key_file_path, 0o600)
                    print(f"Wrote SSH key to {key_file_path}")

                    pubkey_file_path = os.path.expanduser(f"~/.ssh/{key_name}.pub")
                    with open(pubkey_file_path, "w") as pkf:
                        pkf.write(pubkey + "\n")
                    os.chmod(pubkey_file_path, 0o644)
                    print(f"Wrote SSH public key to {pubkey_file_path}")

                #key_file = tempfile.NamedTemporaryFile(mode="w+t")
                #key_file.write(key_data.decode("utf-8"))
                #key_file.flush()
                #key_file.seek(0)
                #key_file_path = key_file.name

                ssh_agent_add_key_file(key_file_path, passphrase)
                print(f"Added SSH key for {cname} with key_id {key_id}")
            except Exception as e:
                print(f"Failed to load SSH key for {cname}: {e}")
                continue


if __name__ == "__main__":

    print("> Starting SSH key loading process...")

    print("> Dumping SSH and Ansible configuration files...")
    dump_ssh_and_ansible_config()

    print("> Loading all ssh keys from vault and injecting into ssh-agent...")
    print("> Using credentials file: " + decrypted_creds_file)
    if not ssh_agent_is_running():
        print("! SSH agent is not running.")
        if not ssh_agent_start():
            print("! Failed to start ssh-agent, exiting.")
            exit(1)

    use_vault = os.environ.get("USE_VAULT", "false").lower() == "true"
    if use_vault:
        ssh_agent_load_keys_from_vault(encrypted_vault_file, password_file)
    else:
        ssh_agent_load_keys_from_credentials_file(decrypted_creds_file)

    ssh_agent_list_keys()
    print(f"SSH_AGENT_SOCK={os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID={os.environ.get('SSH_AGENT_PID')}")
    exit(0)

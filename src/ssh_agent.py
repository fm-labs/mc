import os

from mc import config
from mc.credentials_manager import get_credentials, credentials
from mc.util.ssh_agent_util import ssh_agent_start, ssh_agent_is_running, ssh_agent_list_keys, \
    build_ssh_pkey_from_buffer, pkey_to_openssh_publine, ssh_agent_add_key_file
from ssh_configure import dump_ssh_config


def ssh_agent_load_keys_from_credentials_file(creds_file: str) -> None:
    """Load SSH keys from the given credentials file into the ssh-agent."""

    creds = get_credentials(creds_file, None)
    # iterate creds, find creds with name starting with "sshkey-"
    for cname, cdata in creds.items():
        if not cname.startswith("sshkey-"):
            continue

        print(f"[sshagent] >> Found ssh credential {cname}")
        if "ssh_key" not in cdata:
            print(f"Skipping {cname}, no ssh key data found")
            continue

        key_name = cname[len("sshkey-"):]
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

            ssh_agent_add_key_file(key_file_path, passphrase)
            print(f"Added SSH key for {cname} to ssh-agent successfully.")
        except Exception as e:
            print(f"Failed to load SSH key for {cname}: {e}")
            continue


if __name__ == "__main__":
    vaultfile = config.VAULT_FILE
    vaultpassfile = config.VAULT_PASS_FILE
    encrypt = config.VAULT_ENABLED

    print("[sshagent] Starting SSH agent loader ...")
    print("[sshagent] Dumping SSH config...")
    dump_ssh_config()

    print("[sshagent] Loading all ssh keys from vault and injecting into ssh-agent...")
    if not ssh_agent_is_running():
        print("[sshagent] !! SSH agent is not running.")
        if not ssh_agent_start():
            print("[sshagent] !! Failed to start ssh-agent, exiting.")
            exit(1)

    print("[sshagent] Using credentials file: " + vaultfile)
    if not os.path.exists(vaultfile):
        print(f"[sshagent] !! Credentials vault file does not exist: {vaultfile}")
        exit(1)

    with credentials(mode="r", vaultfile=vaultfile, vaultpassfile=vaultpassfile, encrypt=encrypt) as f:
        ssh_agent_load_keys_from_credentials_file(f.name)

    ssh_agent_list_keys()
    print(f"SSH_AGENT_SOCK={os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID={os.environ.get('SSH_AGENT_PID')}")
    exit(0)

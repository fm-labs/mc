import os

from mc import config
from mc.util.ssh_agent_util import ssh_agent_start, ssh_agent_is_running, ssh_agent_list_keys, \
    ssh_agent_load_keys_from_vault, ssh_agent_load_keys_from_credentials_file
from ssh_configure import dump_ssh_and_ansible_config

encrypted_vault_file = config.VAULT_FILE
password_file = config.VAULT_PASS_FILE

creds_file = f"{encrypted_vault_file}.yaml"

if __name__ == "__main__":

    print("Starting SSH key loading process...")

    print("Dumping SSH and Ansible configuration files...")
    dump_ssh_and_ansible_config()

    print("Loading all ssh keys from vault and injecting into ssh-agent...")
    if not ssh_agent_is_running():
        print("SSH agent is not running.")
        if not ssh_agent_start():
            print("Failed to start ssh-agent, exiting.")
            exit(1)

    use_vault = os.environ.get("USE_VAULT", "false").lower() == "true"
    if use_vault:
        ssh_agent_load_keys_from_vault(encrypted_vault_file, password_file)
    else:
        ssh_agent_load_keys_from_credentials_file(creds_file)

    ssh_agent_list_keys()
    print(f"SSH_AGENT_SOCK={os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID={os.environ.get('SSH_AGENT_PID')}")
    exit(0)

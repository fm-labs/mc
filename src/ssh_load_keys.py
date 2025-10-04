import os

from kloudia import config
from kloudia.util.ssh_agent_util import ssh_agent_start, ssh_agent_is_running, ssh_agent_list_keys, \
    ssh_agent_load_keys_from_vault

encrypted_vault_file = config.VAULT_FILE
password_file = config.VAULT_PASS_FILE

if __name__ == "__main__":

    print("Loading all ssh keys from vault and injecting into ssh-agent...")
    if not ssh_agent_is_running():
        print("SSH agent is not running.")
        if not ssh_agent_start():
            print("Failed to start ssh-agent, exiting.")
            exit(1)

    ssh_agent_load_keys_from_vault(encrypted_vault_file, password_file)
    ssh_agent_list_keys()
    print(f"SSH_AGENT_SOCK={os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID={os.environ.get('SSH_AGENT_PID')}")
    exit(0)

import getpass
import os
import argparse

from mc import config
from mc.credentials import add_ssh_key
from mc.util.ssh_agent_util import ssh_agent_start, ssh_agent_is_running, ssh_agent_list_keys, \
    ssh_agent_load_keys_from_vault, ssh_agent_load_keys_from_credentials_file
from ssh_configure import dump_ssh_and_ansible_config

encrypted_vault_file = config.VAULT_FILE
password_file = config.VAULT_PASS_FILE

creds_file = f"{encrypted_vault_file}.yaml"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add SSH keys to the vault.")
    parser.add_argument('--encrypted', action='store_true', help='Use encrypted vault file')
    args = parser.parse_args()

    # prompt user for key content
    key_name = input("Please enter the name of the key to add: ")
    print("Paste text, then press Ctrl-D (Unix) or Ctrl-Z Enter (Windows).")
    lines = []
    while True:
        try:
            lines.append(input())
        except EOFError:
            break

    key_content = "\n".join(lines)

    #key_content = input("Enter the SSH private key content:\n")
    #key_content = getpass.getpass(prompt="Please enter the content of the key to add: (input hidden) \n")
    #key_passphrase = input("Enter the passphrase for the SSH key (leave blank if none):\n")
    key_passphrase = getpass.getpass("Please enter the passphrase for key content: (input hidden, leave blank if none) \n").strip()

    print("> Starting SSH key addition process...")
    print("key_name:", key_name)
    print("key_content:", key_content)
    print("key_passphrase:", key_passphrase)
    if key_passphrase == "":
        key_passphrase = None

    add_ssh_key(
        path=encrypted_vault_file if args.encrypted else creds_file,
        name=key_name,
        key_content=key_content,
        key_passphrase=key_passphrase if key_passphrase else None
    )
    print("Added SSH key to the vault successfully.")

    exit(0)

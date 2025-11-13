import getpass
import argparse

from mc import config
from mc.credentials_manager import credentials
from mc.sshkey_manager import add_ssh_key

if __name__ == "__main__":
    vaultfile = config.VAULT_FILE
    vaultpassfile = config.VAULT_PASS_FILE

    parser = argparse.ArgumentParser(description="Add SSH keys to the vault.")
    parser.add_argument('--key-path', type=str, help='Path to the SSH private key file', required=False)
    parser.add_argument('--name', type=str, help='Name of the SSH key to add', required=False)
    parser.add_argument('--input', action='store_true', help='Read key content from stdin')
    parser.add_argument('--encrypted', action='store_true', help='Use encrypted vault file')
    args = parser.parse_args()

    key_name = args.name
    if not key_name:
        key_name = input("Please enter the name of the key to add: ")

    key_content = ""
    key_path = args.key_path
    if not key_path:
        # prompt user for key content
        if args.input:
            print("Reading key content from stdin...")
            print("Paste text, then press Ctrl-D (Unix) or Ctrl-Z Enter (Windows).")
            lines = []
            while True:
                try:
                    lines.append(input())
                except EOFError:
                    break
            key_content = "\n".join(lines)
        else:
            key_path = input("Please enter the path to the SSH private key file: ").strip()

    key_passphrase = getpass.getpass("Please enter the passphrase for key content: (input hidden, leave blank if none) \n").strip()

    print("> Starting SSH key addition process...")
    print("key_name:", key_name)
    print("key_path:", key_path)
    print("key_content:", len(key_content), "characters")
    print("key_passphrase:", len(key_passphrase), "characters")

    with credentials(mode="w", vaultfile=vaultfile, vaultpassfile=vaultpassfile, encrypt=args.encrypted) as f:
        print(f"> Using temporary credentials file: {f.name}")
        add_ssh_key(
            f,
            name=key_name,
            key_content=key_content,
            key_passphrase=key_passphrase if key_passphrase else None
        )
        print("Added SSH key to the vault successfully.")

    exit(0)

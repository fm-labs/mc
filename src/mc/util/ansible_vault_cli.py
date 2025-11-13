# Install on MacOS with Homebrew
# brew tap hashicorp/tap
# brew install hashicorp/tap/vault
#
# https://developer.hashicorp.com/vault/install#linux
import os
import shutil
import subprocess

def check_files(vault_file: str, password_file: str) -> None:
    if not vault_file:
        raise RuntimeError("Vault file not specified.")
    if not os.path.isfile(vault_file):
        raise RuntimeError(f"Vault file not found: {vault_file}")
    if not password_file:
        raise RuntimeError("Password file not specified.")
    if not os.path.isfile(password_file):
        raise RuntimeError(f"Password file not found: {password_file}")
        

def ensure_ansible_vault_available():
    if shutil.which("ansible-vault") is None:
        raise RuntimeError("Error: 'ansible-vault' is not in PATH. Please install Ansible or add it to PATH.")
        

def ansible_vault_cli_encrypt(decrypted_file: str, password_file: str, output_file: str) -> str:
    cmd = [
        "ansible-vault",
        "encrypt",
        decrypted_file,
        "--vault-password-file",
        password_file,
        "--output", output_file
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Encrypted vault file successfully.")
        return result.stdout
    except subprocess.CalledProcessError as exc:
        print("Encryption failed", exc.stderr)
        raise RuntimeError(f"ansible-vault encrypt failed with exit code {exc.returncode}")


def ansible_vault_cli_decrypt(encrypted_file: str, password_file: str, output_file: str) -> str:
    cmd = [
        "ansible-vault",
        "decrypt",
        encrypted_file,
        "--vault-password-file",
        password_file,
        "--output", output_file
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Decrypted vault file successfully.")
        return result.stdout
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ansible-vault decrypt failed with exit code {exc.returncode}")

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
        

def ansible_vault_encrypt(vault_file: str, password_file: str, encrypted_vault_file: str) -> None:
    run_ansible_vault("encrypt", vault_file, password_file, encrypted_vault_file)


def ansible_vault_decrypt(vault_file: str, password_file: str, decrypted_vault_file: str) -> None:
    run_ansible_vault("decrypt", vault_file, password_file, decrypted_vault_file)


def run_ansible_vault(mode: str, vault_file: str, password_file: str, output_file: str) -> str:
    """
    Run ansible-vault to encrypt or decrypt a vault file.

    :param mode: "encrypt" or "decrypt"
    :param vault_file: Path to the vault file to encrypt/decrypt
    :param password_file: Path to the file containing the vault password
    :param output_file: Path to write the output file
    :return: stdout from the ansible-vault command
    :raises RuntimeError: if ansible-vault is not available or command fails
    """
    ensure_ansible_vault_available()
    check_files(vault_file, password_file)

    action_label = "Encrypting" if mode == "encrypt" else "Decrypting"
    print(f"{action_label} ansible vault using file: {vault_file} and password file: {password_file}, output to: {output_file}")

    cmd = [
        "ansible-vault",
        mode,
        vault_file,
        "--vault-password-file",
        password_file,
        "--output", output_file
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"{'Encrypted' if mode == 'encrypt' else 'Decrypted'} vault file: {vault_file}")
        return result.stdout
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ansible-vault {mode} failed with exit code {exc.returncode}")

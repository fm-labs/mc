from __future__ import annotations

import hashlib
import io
import os
from typing import Tuple, Any

import paramiko
from paramiko import RSAKey, ECDSAKey, Ed25519Key, PasswordRequiredException, SSHException


def ssh_key_load_with_fingerprint(key_path: str, password=None) -> Tuple[paramiko.PKey, str, Any]:
    """
    Load SSH private key from file and compute its fingerprint.
    If the key is encrypted, a password is required.

    :param key_path: Path to the SSH private key file.
    :param password: Password for the SSH key if it is encrypted.
    :return: Tuple containing the key object, its fingerprint, and the key class.
    """
    for key_class in [RSAKey, ECDSAKey, Ed25519Key]:
        try:
            key = key_class.from_private_key_file(key_path, password=password)
            fingerprint = ':'.join(f'{b:02x}' for b in key.get_fingerprint())
            return key, fingerprint, key_class
        except PasswordRequiredException:
            print("Error: SSH key is encrypted but no passphrase was provided.")
            raise
        except SSHException:
            continue
    raise ValueError("Unsupported or invalid key type.")


def ssh_key_read(key_path: str = None) -> tuple[bytes, str]:
    """
    Read SSH private key from file and compute its SHA-256 hash.
    This method read the raw key data without parsing it.

    :param key_path: Path to the SSH private key file.
    :return: Tuple containing the key data and its SHA-256 hash.
    """

    if not key_path:
        raise ValueError("Error: SSH key path not provided.")

    if not os.path.exists(key_path):
        raise FileNotFoundError(f"SSH key file not found: {key_path}")

    with open(os.path.expanduser(key_path), "rb") as f:
        key_data = f.read()
    if not key_data:
        raise ValueError("Error: SSH key file is empty.")

    key_hash = ssh_key_calculate_hash(key_data)
    return key_data, key_hash


def ssh_key_calculate_hash(key_data: bytes) -> str:
    """Calculate SHA-256 hash of the SSH key data."""
    return hashlib.sha256(key_data).hexdigest()


def ssh_pkey_from_bytes(key_bytes: bytes, password: str = None) -> paramiko.PKey:
    """
    Construct a Paramiko PKey object from SSH key bytes.

    :param key_bytes: SSH private key data in bytes.
    :param password: Password for the SSH key if it is encrypted.
    :return: Paramiko PKey object.
    """
    key_str = key_bytes.decode("utf-8")
    key_stream = io.StringIO(key_str)

    for key_class in [RSAKey, ECDSAKey, Ed25519Key]:
        try:
            pkey = key_class.from_private_key(key_stream, password=password)
            return pkey
        except PasswordRequiredException:
            print("Error: SSH key is encrypted but no passphrase was provided.")
            raise
        except SSHException:
            key_stream.seek(0)
            continue
    raise ValueError("Unsupported or invalid key type.")


def sftp_copy_file(
    ssh_client: paramiko.SSHClient,
    local_path: str,
    remote_path: str
) -> None:
    """
    Copy a file to a remote host using SCP over an established SSH connection.

    :param ssh_client: An established Paramiko SSHClient connection.
    :param local_path: Path to the local file to be copied.
    :param remote_path: Destination path on the remote host.
    """
    with ssh_client.open_sftp() as sftp:
        sftp.put(local_path, remote_path)


def sftp_mkdir(
    ssh_client: paramiko.SSHClient,
    remote_path: str,
    mode: int = 0o755
) -> None:
    """
    Create a directory on the remote host via an established SSH connection.

    :param ssh_client: An established Paramiko SSHClient connection.
    :param remote_path: Path of the directory to create on the remote host.
    :param mode: Permissions mode for the new directory.
    """
    with ssh_client.open_sftp() as sftp:
        try:
            sftp.mkdir(remote_path, mode=mode)
        except IOError as e:
            if e.errno == 17:  # File exists
                pass
            else:
                raise


def ssh_mkdir_recursive(
    ssh_client: paramiko.SSHClient,
    remote_path: str,
    mode: int | None = None # 0o755
) -> None:
    """
    Ensure a directory exists on the remote host using SSH command execution.

    :param ssh_client: An established Paramiko SSHClient connection.
    :param remote_path: Path of the directory to ensure on the remote host.
    :param mode: Permissions mode for the directory.
    """
    command = f"mkdir -p {remote_path}"
    if mode is not None:
        command += f" && chmod {oct(mode)[2:]} {remote_path}"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        raise RuntimeError(f"Failed to ensure directory '{remote_path}': {error_msg}")

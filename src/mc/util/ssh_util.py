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
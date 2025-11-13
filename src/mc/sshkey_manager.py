from __future__ import annotations

import os
from tempfile import NamedTemporaryFile

from paramiko import PasswordRequiredException

from mc.credentials_manager import add_credentials, remove_credentials
from mc.util.ssh_util import ssh_key_read, ssh_key_load_with_fingerprint, ssh_pkey_from_bytes


def add_ssh_key(credsfile: str, name: str,
                key_file: str | None = None, key_content: str | None = None,
                key_passphrase: str = None, key_passphrase_file: str = None,
                allow_overwrite: bool = False) -> None:
    """
    Add an SSH private key to the credentials store.

    :param credsfile: Path to the credentials file.
    :param name: Name of the SSH key entry.
    :param key_file: Path to the SSH private key file.
    :param key_content: Content of the SSH private key as a string.
    :param key_passphrase: Passphrase for the SSH private key (if encrypted).
    :param key_passphrase_file: Path to a file containing the passphrase.
    :param allow_overwrite: Whether to allow overwriting an existing entry with the same name.
    :raises ValueError: If neither key_file nor key_content is provided, or if loading
    """

    if not key_file and not key_content:
        raise ValueError("Either key_path or key_content must be provided.")

    if key_content:
        # Write key content to a temporary file for processing
        with NamedTemporaryFile(mode="w", delete=False) as tmp_key_file:
            tmp_key_file.write(key_content)
            tmp_key_file_path = tmp_key_file.name
        key_file = tmp_key_file_path
    else:
        key_file = os.path.expanduser(key_file)

    if key_passphrase is None and key_passphrase_file:
        key_passphrase_file = os.path.expanduser(key_passphrase_file)
        if not os.path.exists(key_passphrase_file):
            raise ValueError(f"Passphrase file does not exist: {key_passphrase_file}")
        with open(key_passphrase_file, "r") as pf:
            key_passphrase = pf.read().strip()

    # Try to load the key to verify it's valid and get the key fingerprint
    try:
        print(f"Loading key from {key_file}")
        ssh_key_bytes, ssh_key_hash = ssh_key_read(key_file)
        pkey, fingerprint, key_class = ssh_key_load_with_fingerprint(key_file, password=key_passphrase)
        print(f"Loaded SSH key with fingerprint: {fingerprint}, hash: {ssh_key_hash}, type: {key_class.__name__}")
    except Exception as e:
        raise ValueError(f"Error loading SSH key: {e}")

    #cname = f"ssh-key-{ssh_key_hash[:16]}"
    cname = f"sshkey-{name}"
    creds = {
             #"ssh_key_name": name,
             #"ssh_key_type": key_class.__name__.lower()[:-3],  # e.g. RSAKey -> rsa
             #"ssh_key_hash": ssh_key_hash,
             #"ssh_key_fingerprint": fingerprint,
             "ssh_key": ssh_key_bytes,
             }
    if key_passphrase:
        creds["ssh_key_passphrase"] = key_passphrase

    add_credentials(credsfile, cname, creds, allow_overwrite=allow_overwrite)

    # test pkey construction with the creds
    try:
        # Decode bytes to text
        #key_str = ssh_key_bytes.decode("utf-8")
        #key_stream = io.StringIO(key_str)
        #pkey = key_class.from_private_key(key_stream, password=key_passphrase)
        #print(f"Test: reconstructed PKey from stored data, fingerprint: {pkey.get_fingerprint().hex()}")
        ssh_pkey_from_bytes(ssh_key_bytes, password=key_passphrase)
    except PasswordRequiredException:
        print("Warning: could not reconstruct PKey from stored data: passphrase required.")
        raise
    except Exception as e:
        print(f"Warning: could not reconstruct PKey from stored data: {e}")
        raise


def remove_ssh_key(credsfile: str, name: str) -> None:
    """Remove an SSH key from the credentials store by name."""
    remove_credentials(credsfile, f"sshkey-{name}")


# def lookup_ssh_key_passphrase(path: str, key_path: str = None, key_id=None) -> str | None:
#     if not key_path and not key_id:
#         raise ValueError("Either key_path or key_id must be provided.")
#
#     if key_path:
#         _, key_id = ssh_key_read(key_path)
#
#     data, _ = load_credentials(path)
#     cname = f"ssh-key-{key_id[:16]}"
#     if cname in data:
#         entry = data[cname]
#         if entry.get("ssh_key_id") != key_id:
#             raise RuntimeError(f"Error: credential '{cname}' has mismatched key_id.")
#
#         if isinstance(entry, dict):
#             return entry.get("ssh_key_passphrase")
#
#     # Fallback: search all entries for matching key_id
#     for name, entry in data.items():
#         if not isinstance(entry, dict):
#             continue
#         if entry.get("ssh_key_id") == key_id:
#             return entry.get("ssh_key_passphrase")
#     return None

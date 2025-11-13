import os
import sys
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Iterator, IO

from mc.util.ansible_vault_cli import ansible_vault_cli_decrypt, ansible_vault_cli_encrypt


@contextmanager
def open_vaultfile(encrypted_file: str, mode: str = "r", passfile: str = None, password: str = None,
                   password_callback=None, create=False) -> Iterator[IO]:
    """
    Context manager to open an Ansible Vault file, decrypting it for read/write access,
    and re-encrypting it on exit if in write mode.
    """
    print("Entering vault file context manager...", encrypted_file, mode, passfile, create)

    if not encrypted_file:
        raise ValueError("vaultfile must be specified")
    if mode not in ("r", "w"):
        raise ValueError("mode must be 'r' or 'w'")

    do_decrypt = True
    if not os.path.exists(encrypted_file):
        if mode == "r":
            raise FileNotFoundError(f"Vault file does not exist: {encrypted_file}")
        elif mode == "w" and not create:
            raise FileNotFoundError(f"Vault file does not exist: {encrypted_file}")
        elif mode == "w" and create:
            do_decrypt = False


    def _create_tmp_password_file(pw: bytes|str) -> str:
        if not isinstance(pw, (str, bytes)):
            raise ValueError("password must be a string or bytes")
        if isinstance(pw, str):
            pw = pw.strip().encode("utf-8")
        tmp_pw_file = NamedTemporaryFile()
        tmp_pw_file.write(pw)
        tmp_pw_file.flush()
        tmp_pw_file.seek(0)
        return tmp_pw_file.name

    if not passfile:
        if password:
            passfile = _create_tmp_password_file(password)
        elif password_callback is not None:
            # check if ask_password is callable
            if not callable(password_callback):
                raise ValueError("ask_password must be a callable function")

            pw = password_callback(prompt="Enter password for vault file")
            passfile = _create_tmp_password_file(pw)
        else:
            raise ValueError("Either password, passfile, or ask_password must be provided")

    decrypted_file = NamedTemporaryFile()
    if do_decrypt:
        try:
            ansible_vault_cli_decrypt(encrypted_file, passfile, decrypted_file.name)
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt vault file: {e}") from e

    error = False
    try:
        yield decrypted_file  # what becomes `f` in the with-block
    except Exception as e:
        error = True
        raise
    finally:
        if not error and mode == "w":
            try:
                print("Re-encrypting vault file...")
                ansible_vault_cli_encrypt(decrypted_file.name, passfile, encrypted_file)
            except Exception as e:
                print(f"Warning: Failed to re-encrypt vault file: {e}", file=sys.stderr)
                raise
    print("Closing vault file context manager.")
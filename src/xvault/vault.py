import os
import sys
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Optional, AsyncGenerator, Generator, Callable

from xvault.backend.ansible_vault import run_ansible_vault


@contextmanager
def open_vaultfile(vaultfile: str, mode: str = "r", password: str = None, passfile: str = None, ask_password=None, create=False) -> Generator:
    """
    Context manager to open an Ansible Vault file, decrypting it for read/write access,
    and re-encrypting it on exit if in write mode.
    """
    if not vaultfile:
        raise ValueError("vaultfile must be specified")
    if mode not in ("r", "w"):
        raise ValueError("mode must be 'r' or 'w'")

    do_decrypt = True
    if not os.path.exists(vaultfile):
        if mode == "r":
            raise FileNotFoundError(f"Vault file does not exist: {vaultfile}")
        elif mode == "w" and not create:
            raise FileNotFoundError(f"Vault file does not exist: {vaultfile}")
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

    if password:
        passfile = _create_tmp_password_file(password)
    elif not passfile and ask_password is not None:
        # check if ask_password is callable
        if not callable(ask_password):
            raise ValueError("ask_password must be a callable function")

        pw = ask_password(prompt="Enter password for vault file")
        passfile = _create_tmp_password_file(pw)

    if not passfile:
        raise ValueError("Either password, passfile, or ask_password must be provided")

    decrypted_file = NamedTemporaryFile()
    if do_decrypt:
        try:
            run_ansible_vault("decrypt", vaultfile, passfile, decrypted_file.name)
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
                run_ansible_vault("encrypt", decrypted_file.name, passfile, vaultfile)
            except Exception as e:
                print(f"Warning: Failed to re-encrypt vault file: {e}", file=sys.stderr)
                raise
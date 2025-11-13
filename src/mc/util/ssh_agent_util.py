import io
import os
import re
import subprocess

import paramiko
import pexpect
from paramiko import RSAKey, ECDSAKey, Ed25519Key


def ssh_agent_start():
    """
    Starts the ssh-agent and sets the necessary environment variables.
    """
    try:
        print("Starting ssh-agent")
        # Start the ssh-agent
        p = subprocess.run(["ssh-agent", "-s"], check=True, capture_output=True, text=True)
        agent_output = p.stdout
        agent_error = p.stderr
        if agent_error:
            print(f"ssh-agent error: {agent_error}")
            return False
        print("ssh-agent started.", agent_output)

        # Parse the output to extract environment variables
        for line in agent_output.splitlines():
            if line.startswith("SSH_AUTH_SOCK"):
                ssh_auth_sock = line.split(";")[0].split("=")[1]
                os.environ["SSH_AUTH_SOCK"] = ssh_auth_sock
            elif line.startswith("SSH_AGENT_PID"):
                ssh_agent_pid = line.split(";")[0].split("=")[1]
                os.environ["SSH_AGENT_PID"] = ssh_agent_pid

        return True
    except Exception as e:
        print(f"Failed to start ssh-agent: {e}")
        return False


def ssh_agent_is_running() -> bool:
    """
    Checks if the ssh-agent is running by verifying the SSH_AUTH_SOCK environment variable.
    """
    ssh_auth_sock = os.environ.get("SSH_AUTH_SOCK")
    if not ssh_auth_sock:
        return False
    if not os.path.exists(ssh_auth_sock):
        return False

    ssh_agent_pid = os.environ.get("SSH_AGENT_PID")
    if not ssh_agent_pid:
        return False
    try:
        os.kill(int(ssh_agent_pid), 0)  # Check if process exists
    except OSError:
        return False
    return True


def ssh_agent_list_keys() -> list:
    """
    Lists the keys currently loaded in the ssh-agent.
    """
    try:
        p = subprocess.run(["ssh-add", "-l"], check=True, capture_output=True, text=True)
        output = p.stdout
        error = p.stderr
        if error:
            print(f"ssh-add error: {error}")
            return []
        keys = []
        for line in output.splitlines():
            match = re.match(r"(\d+)\s+([a-f0-9:]+)\s+(.+)", line)
            if match:
                bits, fingerprint, comment = match.groups()
                keys.append({"bits": bits, "fingerprint": fingerprint, "comment": comment})
        return keys
    except subprocess.CalledProcessError as e:
        if e.returncode == 1 and "The agent has no identities." in e.stderr:
            return []  # No keys loaded
        print(f"Failed to list ssh-agent keys: {e.stderr}")
        return []
    except Exception as e:
        print(f"Failed to list ssh-agent keys: {e}")
        return []


def ssh_agent_add_key_file(key_file: str, key_passphrase: str):
    """
    Injects an SSH key into the ssh-agent using ssh-add.
    """
    key_file = os.path.expanduser(key_file)
    if not os.path.exists(key_file):
        print(f"SSH key file does not exist: {key_file}")
        return False

    try:
        if key_passphrase:
            # Use pexpect to handle the passphrase prompt
            child = pexpect.spawn(f"ssh-add {key_file}")
            child.expect("Enter passphrase for .*:")
            child.sendline(key_passphrase)
            child.expect(pexpect.EOF)
            print(f"Added protected SSH key {key_file} to ssh-agent.")
        else:
            child = pexpect.spawn(f"ssh-add {key_file}")
            child.expect(pexpect.EOF)
            print(f"Added unprotected SSH key {key_file} to ssh-agent.")
    except Exception as e:
        print(f"ssh-add failed: {e}")
        raise


def build_ssh_pkey_from_buffer(key_data: bytes, passphrase: str | None) -> paramiko.PKey:
    # Decode bytes to text
    key_str = key_data.decode("utf-8")
    key_stream = io.StringIO(key_str)

    for key_class in [RSAKey, ECDSAKey, Ed25519Key]:
        try:
            return key_class.from_private_key(key_stream, password=passphrase)
        except Exception:
            key_stream.seek(0) # rewind
            continue

    raise ValueError("Unsupported key type or incorrect passphrase")


def pkey_to_openssh_publine(pkey, comment: str | None = None) -> str:
    """
    Return the OpenSSH public key line for a Paramiko PKey (RSA, ECDSA, Ed25519, etc.).
    Example output: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... user@host"
    """
    keytype = pkey.get_name()      # e.g. "ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256"
    b64 = pkey.get_base64()        # base64 of the public blob
    suffix = f" {comment}" if comment else ""
    return f"{keytype} {b64}{suffix}"


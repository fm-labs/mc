import os
from typing import Optional
import paramiko
from paramiko import PasswordRequiredException, RSAKey, ECDSAKey, Ed25519Key, AuthenticationException
from paramiko.config import SSHConfigDict

from rx.util import split_url

# @dataclass
# class SSHParams:
#     hostname: str
#     port: int = 22
#     user: str = None
#     password: str = None
#     key_file: str = None
#     key_passphrase: str = None


def ssh_params_from_url(ssh_url, ssh_params: dict = None, use_ssh_config=True) -> dict:
    """
    Extract SSH connection parameters from destination URL.
    Supports loading additional parameters from ~/.ssh/config if use_ssh_config is True.
    Merges with provided ssh_params dictionary.

    :param ssh_url: Expected format: ssh://[user@]host[:port][/path]
    :param ssh_params: Optional dictionary of SSH parameters to override.
    :param use_ssh_config: Whether to load parameters from ~/.ssh/config.
    :return: Dictionary of SSH connection parameters.
        The dictionary may contain keys: hostname, port, username, password, key_filename, key_passphrase.
        The keys matches the parameters of paramiko.SSHClient.connect().
    """
    [_, host] = split_url(ssh_url)
    user = None
    if "@" in host:
        [user, host] = host.split("@", 1)
    if ":" in host:
        [host, _] = host.split(":", 1) # remove the path if any

    _params = {
        "hostname": host,
        "port": 22,
        "username": user,
    }
    # load from ssh config if enabled
    if use_ssh_config:
        ssh_host_config = ssh_load_host_config(host)
        print(f"SSH host config for {host}: {ssh_host_config}")
        if ssh_host_config:
            if "hostname" in ssh_host_config:
                _params["hostname"] = ssh_host_config["hostname"]
            if "port" in ssh_host_config:
                _params["port"] = int(ssh_host_config["port"])
            if "user" in ssh_host_config and not user:
                _params["username"] = ssh_host_config["user"]
            if "identityfile" in ssh_host_config:
                _params["key_filename"] = ssh_host_config["identityfile"][0]

    # override with provided ssh_params
    if ssh_params:
        _params.update(ssh_params)
    return _params


def ssh_load_host_config(host: str) -> SSHConfigDict:
    """
    Load SSH configuration for a specific host from the user's ~/.ssh/config file.
    Respects the SSH_CONFIG_FILE environment variable if set.

    :param host: The hostname or alias to look up in the SSH config.
    :return: A dictionary of SSH configuration options for the specified host.
    """

    ssh_config = paramiko.SSHConfig()
    ssh_config_path = os.getenv("SSH_CONFIG_FILE", "~/.ssh/config")
    ssh_config_path = os.path.expanduser(ssh_config_path)
    if os.path.exists(ssh_config_path):
        print(f"Loading SSH config from {ssh_config_path}")
        with open(ssh_config_path) as f:
            ssh_config.parse(f)

    host_config = ssh_config.lookup(host) or {}
    print("Found SSH config for host {}: {}".format(host, host_config))
    return host_config


def ssh_connect(hostname, port=22, username: str = None, password: str = None,
                key_filename: str = None, key_passphrase: str = None,
                key_passphrase_callback: Optional[callable] = None,
                use_agent_keys=True,
                timeout=30) -> paramiko.SSHClient:
    """
    Establish an SSH connection to a remote host.
    Respects user's ~/.ssh/config for host-specific settings.
    Loads keys from the SSH agent if available.

    :param hostname: The hostname or IP address of the remote host.
    :param port: The SSH port of the remote host (default is 22).
    :param username: The username to authenticate as.
    :param password: The password to authenticate with (if not using key).
    :param key_filename: The path to the private key file (if using key).
    :param key_passphrase: The passphrase for the private key (if the key is password-protected).
    :param key_passphrase_callback: A callable that returns the passphrase for the private key.
    :param use_agent_keys: Whether to attempt authentication using keys loaded in the SSH agent.
    :param timeout: Connection timeout in seconds.
    :return: An established Paramiko SSHClient instance.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_params = {}
    ssh_params = ssh_params_from_url(hostname, use_ssh_config=True)
    print("SSH connection params", ssh_params)

    hostname = ssh_params.get("hostname", hostname)
    port = int(ssh_params.get("port", port))
    username = username or ssh_params.get("username")
    key_filename = key_filename or ssh_params.get("key_filename")

    key_passphrase = key_passphrase or ssh_params.get("key_passphrase")
    if not key_passphrase and key_passphrase_callback and callable(key_passphrase_callback):
       key_passphrase = key_passphrase_callback(key_filename)

    try:
        print("Connecting to {}@{}:{}. Using keyfile={}".format(username, hostname, port, key_filename))

        pkey = None
        if key_filename:
            pkey, fingerprint = ssh_load_pkey(key_filename, key_passphrase)

        client.connect(hostname=hostname, port=port,
                       username=username, password=password,
                       key_filename=key_filename, passphrase=key_passphrase,
                       pkey=pkey,
                       auth_timeout=10,
                       timeout=timeout)
        return client
    except PasswordRequiredException:
        if not key_passphrase:
            print("Private key is password-protected, but no key_passphrase provided. Trying agent keys...")

        if use_agent_keys:
            ssh_agent = paramiko.Agent()
            agent_keys = ssh_agent.get_keys()
            if len(agent_keys) == 0:
                raise Exception("No keys in SSH agent and key is encrypted.")

            for i, agent_key in enumerate(agent_keys):
                try:
                    print(agent_key)
                    print(f"Trying to authenticate with agent key {i}: {agent_key.get_fingerprint().hex()}")
                    client.connect(hostname=hostname, port=port, username=username,
                                   pkey=agent_key, timeout=timeout)
                    return client
                except AuthenticationException:
                    print("❌ Authentication failed with this key.")
                    continue
                except Exception as e:
                    print(f"❌ Error using agent key: {e}")
                    continue
            raise Exception("All keys in SSH agent failed to authenticate.")

        raise("Private key is password-protected, but no key_passphrase provided, and no agent keys available.")
    except Exception as e:
        print(f"Failed to connect to {hostname}:{port} - {e}")
        raise


def ssh_load_pkey(key_filename: str, key_passphrase: str) -> tuple[paramiko.PKey, str]:
    """
    Unlock a password-protected private key file.
    If no password is provided, it will attempt to load the key without a password.

    :param key_filename: The path to the private key file.
    :param key_passphrase: The password for the private key.
    :return: A Paramiko PKey instance. Also returns the key fingerprint as a hex string.
    :raises PasswordRequiredException: If the key is password-protected and no password is provided.
    :raises SSHException: If the key file is invalid or cannot be loaded.
    """
    print("Trying to unlock private key '{}'".format(key_filename))
    for key_class in (RSAKey, ECDSAKey, Ed25519Key):
        try:
            pkey = key_class.from_private_key_file(key_filename, password=key_passphrase)
            fingerprint = ':'.join(f'{b:02x}' for b in pkey.get_fingerprint())
            print(f"Unlocked {key_class.__name__} key with fingerprint: {fingerprint}")
            return pkey, fingerprint
        except PasswordRequiredException:
            print(f"{key_class.__name__} is password-protected, but no password provided.")
            raise
        except paramiko.SSHException:
            print(f"Key file '{key_filename}' is not a valid {key_class.__name__} key or wrong passphrase.")
            continue
    raise Exception("Unsupported or invalid key file.")


def ssh_execute_command(client, command: str, timeout: int = None, environment: dict = None) -> tuple[bytes, bytes, int]:
    """
    Execute a command on the remote host via an established SSH connection.

    :param client: An established Paramiko SSHClient instance.
    :param command: The command to execute on the remote host.
    :param timeout: Optional timeout for command execution.
    :param environment: Optional dictionary of environment variables to set for the command.
    :return: A tuple of (stdout, stderr, exit_status).
    """
    if environment is None:
        environment = {}
    try:
        print("Executing command via SSH: {}".format(command))
        stdin, stdout, stderr = client.exec_command(command,
                                                    get_pty=True,
                                                    timeout=timeout,
                                                    environment=environment)
        exit_status = stdout.channel.recv_exit_status()
        return stdout.read(), stderr.read(), exit_status
    except Exception as e:
        print(f"ssh_execute_command ERROR: '{command}': {e}")
        raise

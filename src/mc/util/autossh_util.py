import os
import sys
import subprocess
from pathlib import Path
from typing import Callable, Optional, List


def echoerr(msg: str) -> None:
    print(msg, file=sys.stderr)


def echolog(msg: str) -> None:
    print(msg)


def process_is_alive(pid: int) -> bool:
    """
    Return True if a process with PID `pid` exists and we can signal it.
    Works on Unix via signal 0. On Windows, this may raise if PID is invalid.
    """
    try:
        # signal 0 doesn't actually send a signal, but performs error checking
        os.kill(pid, 0)
    except ProcessLookupError:
        return False  # no such process
    except PermissionError:
        return True  # process exists but we don't have permission
    except OSError:
        return False
    else:
        return True


def setup_autossh_tunnel(
        remote_host: str,
        remote_user: str,
        pid_file: str,
        local_forward_specs: Optional[List[str]] = None,
        remote_forward_specs: Optional[List[str]] = None,
        load_ssh_key: Callable[[], bool] = None,
        env: Optional[dict] = None
) -> int:
    """
    Start an autossh local port/socket forward and write its PID to a file,
    unless it's already running.

    Args:
        remote_host: hostname or IP of the remote SSH server.
        remote_user: SSH username on the remote server.
        pid_file: path to write the autossh PID file.
        local_forward_specs: list of local forward specs.
        remote_forward_specs: list of remote forward specs.
        load_ssh_key: a callable that returns True on success, False on failure.
                      This should perform any SSH-agent setup/unlock you need.
        env: optional environment dict to read values from; defaults to os.environ.

    Returns:
        The PID of the started autossh process, or None on failure.
    """

    if not remote_host:
        raise ValueError("remote_host not defined. Exiting")
    if not remote_user:
        raise ValueError("remote_user not defined. Exiting")
    if not pid_file:
        raise ValueError("pid_file not defined. Exiting")

    env = os.environ if env is None else env
    autossh_bin = env.get("AUTOSSH_BIN", "autossh")
    #base_ssh_args = env.get("SSH_ARGS", "").strip()
    ssh_key = env.get("SSH_REMOTE_SSH_KEY", "").strip()

    # If a tunnel is already running, exit successfully.
    pid_path = Path(pid_file)
    if pid_path.exists():
        try:
            existing_pid = int(pid_path.read_text().strip())
        except ValueError:
            existing_pid = None

        if existing_pid and process_is_alive(existing_pid):
            echoerr(f"SSH tunnel already up. PID: {existing_pid}")
            return True

    # Load / unlock the SSH key (delegated to caller to match bash `load_ssh_key`)
    if load_ssh_key and not load_ssh_key():
        raise RuntimeError("Failed to load SSH key. Exiting")

    # Compose SSH arguments
    ssh_args_list = []
    #if base_ssh_args:
    #    # Split respecting quotes, like a shell would
    #    ssh_args_list.extend(shlex.split(base_ssh_args))

    if ssh_key:
        ssh_args_list.extend(["-o", "IdentitiesOnly=yes", "-i", ssh_key])

    echolog(f"Setting up autossh tunnel to {remote_host}")

    # Build autossh command (equivalent to: autossh -M 0 -N -L local:remote [SSH_ARGS] user@host)

    forward_spec = []
    for lspec in (local_forward_specs or []):
        forward_spec.append("-L")
        forward_spec.append(lspec)
    for rspec in (remote_forward_specs or []):
        forward_spec.append("-R")
        forward_spec.append(rspec)

    cmd = [autossh_bin, "-M", "0", "-N"]
    cmd.extend(forward_spec)
    cmd.extend(ssh_args_list)
    cmd.append(f"{remote_user}@{remote_host}")

    echolog(f"Starting autossh with command: {' '.join(cmd)}")
    # Launch in background, detach from our stdio (like '&' in bash)
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # detach process group (POSIX)
        )
    except FileNotFoundError:
        echoerr(f"Failed to start autossh: '{autossh_bin}' not found. Exiting")
        return False
    except Exception as e:
        echoerr(f"Failed to start autossh: {e}")
        return False

    ssh_pid = proc.pid
    echolog(f"SSH PID: {ssh_pid}")

    # Check the process is alive (similar to `kill -0`)
    if not process_is_alive(ssh_pid):
        echoerr("SSH tunnel failed to start. Exiting")
        return False

    try:
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(ssh_pid) + "\n")
    except Exception as e:
        echoerr(f"Failed to write PID file '{pid_file}': {e}")
        return False

    # Read back the saved PID for logging
    try:
        saved_pid = pid_path.read_text().strip()
    except Exception:
        saved_pid = str(ssh_pid)

    echolog(f"Tunnel started. PID: {saved_pid}/{ssh_pid}")
    return ssh_pid

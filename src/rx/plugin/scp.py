from pathlib import Path

from rx.config import RunConfig, GlobalContext
from rx.helper.subprocess_helper import rx_subprocess
from rx.util import split_url, get_tool_path


def check_scp_installed(ctx: GlobalContext = None) -> None:
    if not get_tool_path("scp"):
        raise EnvironmentError("scp is not installed or not found in PATH.")


def handle_scp_run(run_cfg: RunConfig, ctx: GlobalContext):
    src = run_cfg.src
    dest = run_cfg.dest

    # ensure scp cli is installed
    check_scp_installed(ctx)

    [srcschema, src_hostpath] = split_url(src)
    if srcschema not in ["file"]:
        raise ValueError("Source URL must start with file://")
    srcpath = Path(ctx.cwd) / src_hostpath
    if not srcpath.exists():
        raise FileNotFoundError(f"Source path '{srcpath}' does not exist.")
    _src: str = str(srcpath.absolute())

    [destschema, dest_hostpath] = split_url(dest)
    if destschema not in ["scp", "ssh"]:
        raise ValueError("Destination schema not supported, must be scp:// or ssh://")

    # ssh specific options
    ssh_cfg = run_cfg.extra.get("scp", {})
    ssh_port = ssh_cfg.get("port", "22")
    ssh_key_file = ssh_cfg.get("key_file", "")
    ssh_connect_timeout = ssh_cfg.get("connect_timeout", 10)

    cmd = ["scp", "-r"]
    # timeout for ssh connection
    cmd += ["-o", f"ConnectTimeout={ssh_connect_timeout}"]
    # disable host key checking
    cmd += ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
    if ssh_key_file:
        cmd += ["-i", ssh_key_file]
    if ssh_port and ssh_port != "22":
        cmd += ["-P", str(ssh_port)]

    _src = _src.rstrip("/")
    _dest = dest_hostpath.rstrip("/")

    cmd += [f"{_src}/", f"{_dest}"]
    return rx_subprocess(cmd, cwd=ctx.cwd)


handler = handle_scp_run

from pathlib import Path

from rx.config import RunConfig, GlobalContext
from rx.helper.subprocess_helper import rx_subprocess
from rx.util import split_url, get_tool_path, toolcmd


def check_rsync_installed(ctx: GlobalContext = None) -> None:
    if not get_tool_path("rsync"):
        raise EnvironmentError("Rsync is not installed or not found in PATH.")


def handle_rsync_run(run_cfg: RunConfig, ctx: GlobalContext, mkdir=True):
    src = run_cfg.src
    dest = run_cfg.dest

    # ensure aws cli is installed
    check_rsync_installed(ctx)

    # validate required fields
    [srcschema, src_hostpath] = split_url(src)
    if srcschema == "":
        srcschema = "file"
    if srcschema not in ["file"]:
        raise ValueError("Source URL must start with file://")
    srcpath = Path(ctx.cwd) / src_hostpath
    if not srcpath.exists():
        raise FileNotFoundError(f"Source path '{srcpath}' does not exist.")

    _src: str = str(srcpath.absolute())
    rsync_args = ["-r", "-t", "-z", "-v", "-c"] # recursive, times, compress, verbose, checksum
    #cmd += ["--delete"]

    [destschema, dhostpath] = split_url(dest)
    if destschema in ["rsync+file", "file", ""]:
        if dhostpath == "" or dhostpath == ".":
            dhostpath = Path(ctx.cwd)
        _dest = str(Path(dhostpath).absolute())
    elif destschema in ["rsync+ssh", "ssh", "scp"]:
        # the ssh destpath should be in the format user@host:/path/to/dir
        [_, remote_path] = dhostpath.split(":", 1)
        if remote_path is None or remote_path == "":
            raise ValueError("Remote path is empty in destination.")

        # ssh specific options
        ssh_cfg = run_cfg.extra.get("ssh", {})
        ssh_port = ssh_cfg.get("port", "22")
        ssh_key_file = ssh_cfg.get("key_file", "")

        # build ssh args
        ssh_args = []
        # timeout for ssh connection
        ssh_args += ["-o", "ConnectTimeout=10"]
        # disable host key checking
        ssh_args += ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
        if ssh_key_file:
            ssh_args += ["-i", ssh_key_file]
        if ssh_port and ssh_port != "22":
            ssh_args += ["-p", str(ssh_port)]
        ssh_args_str = f" {' '.join(ssh_args)}"
        rsync_args += ["-e", f"ssh {ssh_args_str}"]

        # ensure remote dir exists
        # rsync >3.2 supports --mkpath option
        # but for compatibility we use --rsync-path "mkdir -p /path/to/dir && rsync"
        if mkdir:
            #rsync_args += ["--mkpath"] # for rsync >= 3.2
            rsync_args += ["--rsync-path", f"mkdir -p {remote_path} && rsync"]

        # handle exclude/include files
        exclude_file = run_cfg.extra.get("exclude", ".exclude")
        if exclude_file:
            exclude_path = Path(ctx.cwd) / exclude_file
            if exclude_path.exists():
                rsync_args += ["--exclude-from", str(exclude_path)]
            else:
                print(f"Warning: exclude file '{exclude_path}' does not exist, ignoring.")

        include_file = run_cfg.extra.get("include", ".include")
        if include_file:
            include_path = Path(ctx.cwd) / include_file
            if include_path.exists():
                rsync_args += ["--include-from", include_file]
            print(f"Warning: include file '{include_path}' does not exist, ignoring.")

        _dest = dhostpath
    else:
        raise NotImplementedError(f"Unsupported destination URL scheme: {destschema}")

    _src = _src.rstrip("/")
    _dest = _dest.rstrip("/")

    rsync_args += [f"{_src}/", f"{_dest}"]
    cmd = toolcmd("rsync", rsync_args)
    return rx_subprocess(cmd, cwd=str(ctx.cwd))


handler = handle_rsync_run

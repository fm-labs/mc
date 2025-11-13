from pathlib import Path

from rx.helper.subprocess_helper import rx_subprocess
from rx.util import split_url, toolcmd


def rsync_execute(src: str, dest: str, mkdir=True, delete=False, exclude: list = None, ssh_config: dict = None, ):
    # validate required fields
    [srcschema, src_hostpath] = split_url(src)
    if srcschema == "":
        srcschema = "file"
    if srcschema not in ["file"]:
        raise ValueError("Source URL must start with file://")

    if src_hostpath == "" or src_hostpath is None or src_hostpath == "/":
        raise ValueError("Source path is empty.")
    srcpath = Path(src_hostpath).resolve()
    if not srcpath.exists():
        raise FileNotFoundError(f"Source path '{srcpath}' does not exist.")

    _src: str = str(srcpath.absolute())
    rsync_args = ["-r", "-t", "-z", "-v", "-c"] # recursive, times, compress, verbose, checksum
    if delete:
        rsync_args += ["--delete"]

    [destschema, dhostpath] = split_url(dest)
    # local rsync
    if destschema in ["rsync+file", "file", ""]:
        _dest = str(Path(dhostpath).resolve().absolute())
        if mkdir:
            Path(_dest).mkdir(parents=True, exist_ok=True)

    # ssh rsync
    elif destschema in ["rsync+ssh", "ssh", "scp"]:
        # the ssh destpath should be in the format user@host:/path/to/dir
        [_, remote_path] = dhostpath.split(":", 1)
        if remote_path is None or remote_path == "":
            raise ValueError("Remote path is empty in destination.")

        # ssh specific options
        ssh_port = ssh_config.get("port", "22")
        ssh_key_file = ssh_config.get("key_file", "")
        ssh_args = []
        ssh_args += ["-o", "ConnectTimeout=10"]
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
        exclude_file = ".dockerignore"
        if exclude_file:
            exclude_path = Path(exclude_file).resolve()
            if exclude_path.exists():
                rsync_args += ["--exclude-from", str(exclude_path)]
            else:
                print(f"Warning: exclude file '{exclude_path}' does not exist, ignoring.")

        #include_file = ""
        #if include_file:
        #    include_path = Path(include_file).resolve()
        #    if include_path.exists():
        #        rsync_args += ["--include-from", include_file]
        #    print(f"Warning: include file '{include_path}' does not exist, ignoring.")

        _dest = dhostpath
    else:
        raise NotImplementedError(f"Unsupported destination URL scheme: {destschema}")

    _src = _src.rstrip("/")
    _dest = _dest.rstrip("/")

    rsync_args += [f"{_src}/", f"{_dest}"]
    cmd = toolcmd("rsync", rsync_args)
    return rx_subprocess(cmd, cwd=str(Path(src).resolve().absolute()))

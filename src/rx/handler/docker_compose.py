import subprocess
from pathlib import Path

from paramiko.client import SSHClient

from rx.config import RunConfig, GlobalContext
from rx.helper.sshpy_helper import ssh_connect, ssh_execute_command, ssh_params_from_url
from rx.helper.subprocess_helper import rx_subprocess
from rx.util import split_url



def run_local_hook_script(local_compose_dir: Path, script_name: str) -> tuple[str, str, int]:
    stdout, stderr, rc = "", "", 0 # default success
    setup_script = local_compose_dir / script_name
    if setup_script.exists() and setup_script.is_file():
        print(f"Found setup.sh script at {setup_script}, executing on remote host...")
        cmd_str = f"chmod +x setup.sh && ./setup.sh"
        print(f"Hook command: {cmd_str}")
        try:
            stdout, stderr, rc = rx_subprocess(cmd_str,
                                               check=True,cwd=str(local_compose_dir),
                                               text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            stdout = e.stdout
            stderr = e.stderr
            rc = e.returncode

        if rc != 0:
            raise RuntimeError(f"{script_name} failed with exit code {rc}")

        print(f"Hook script {script_name} exited with code {rc}")
        print(f"Hook script {script_name} STDOUT: {stdout}")
        print(f"Hook script {script_name} STDERR: {stderr}")
    return stdout, stderr, rc


def run_remote_hook_script(client: SSHClient, remote_compose_dir: str, script_name: str) -> tuple[str, str, int]:
    stdout, stderr, rc = "", "", 0 # default success
    try:
        cmd_str = f"cd {remote_compose_dir} && chmod +x {script_name} && bash ./{script_name}"
        print(f"Remote Hook command: {cmd_str}")
        stdout, stderr, rc = ssh_execute_command(client, cmd_str)
        print(f"{script_name} exited with code {rc}")
    except Exception as e:
        print(f"SSH remote execution error: {e}")
        stdout = ""
        stderr = str(e)
        rc = -1
        raise
    finally:
        print(f"Remote Hook script {script_name} exited with code {rc}")
        print(f"Remote Hook script {script_name} STDOUT: {stdout}")
        print(f"Remote Hook script {script_name} STDERR: {stderr}")
    return stdout, stderr, rc



def build_compose_command(command: list[str], compose_files: list[str], project_dir: str = None,
                          compose_cfg: dict = None) -> list:
    # construct docker compose command to be executed locally or remotely
    # if compose_cfg is None:
    #     compose_cfg = {}
    #
    # composefile_cfg = compose_cfg.get("composefile", "compose.yaml")
    #
    # if composefile_cfg:
    #     if isinstance(composefile_cfg, list):
    #         compose_files = composefile_cfg
    #     elif isinstance(composefile_cfg, str):
    #         compose_files = [composefile_cfg]
    # # auto-detect compose file if not specified
    # if len(compose_files) == 0:
    #     default_compose_files = [
    #         "compose",
    #         "compose.prod",
    #         "compose.override",
    #         "docker-compose",
    #         "docker-compose.prod",
    #         "docker-compose.override",
    #     ]
    #     for f in default_compose_files:
    #         for ext in [".yml", ".yaml"]:
    #             f_ext = f + ext
    #             if (ctx.cwd / shostpath / f_ext).exists():
    #                 compose_files.append(f_ext)

    cmd = ["docker", "compose",
           "--ansi", "never", "--progress", "plain",
           ]

    if project_dir is None:
        cmd += ["-p", project_dir]

    # add compose files
    if len(compose_files) == 0:
        raise FileNotFoundError("Compose file not specified.")
    for cf in compose_files:
        cmd += ["-f", f"{cf}"]

    return cmd + command


def build_compose_up_command(compose_files: list[str], project_dir: str = None, compose_cfg: dict = None) -> list:
    if compose_cfg is None:
        compose_cfg = {}

    cmd = ["up", "-d", "--remove-orphans", "--force-recreate"]
    up_args = compose_cfg.get("up_args", [])
    if not isinstance(up_args, list):
        raise ValueError("compose.up_args must be a list")

    cmd += up_args
    return build_compose_command(cmd, compose_files, project_dir, compose_cfg)



def handle_docker_compose_run(run_cfg: RunConfig, ctx: GlobalContext) -> tuple[str, str, int]:
    src = run_cfg.src
    dest = run_cfg.dest
    ssh_cfg = run_cfg.extra.get("ssh", {})
    compose_cfg = run_cfg.extra.get("compose", {})

    # 1. validate required fields
    allowed_src_schemes = ["file", ]
    [sscheme, shostpath] = split_url(src)
    if sscheme not in allowed_src_schemes:
        raise ValueError(f"Unsupported source URL scheme: {sscheme}."
                         f" Supported schemes: {','.join(allowed_src_schemes)}")

    allowed_dest_schemes = ["ssh", "unix"]
    [dscheme, dhostpath] = split_url(dest)
    if dscheme not in allowed_dest_schemes:
        raise ValueError(f"Unsupported destination URL scheme: {dscheme}."
                         f" Supported schemes: {','.join(allowed_dest_schemes)}")


    local_compose_dir = (ctx.cwd / shostpath).resolve()
    remote_compose_dir = f"~/.compose/{ctx.config.metadata.name}"


    compose_files = []
    _compose_files = compose_cfg.get("composefile", "compose.yaml")
    if _compose_files:
        if isinstance(_compose_files, list):
            compose_files = _compose_files
        elif isinstance(_compose_files, str):
            compose_files = [_compose_files]
    # always add override file if exists
    override_file = local_compose_dir / "compose.override.yaml"
    if override_file.exists() and override_file.is_file():
        compose_files.append("compose.override.yaml")
    # remove duplicates while preserving order
    compose_files = list(dict.fromkeys(compose_files))

    # local deployment
    if dscheme == "unix":
        rsync_dest = Path(remote_compose_dir).resolve()
        rsync_dest.mkdir(parents=True, exist_ok=True)
        upload_directory_via_rsync(local_compose_dir, remote_compose_dir, ssh_cfg, ctx)

        # run setup.sh hook if exists
        if ctx.dry_run:
            print(f"Dry run mode, skipping setup.sh execution on {dest}")
        else:
            run_local_hook_script(rsync_dest, "setup.sh")

        # prepend local compose dir to compose files
        compose_files = [str(local_compose_dir / cf) for cf in compose_files]
        docker_cmd = build_compose_up_command(compose_files, str(rsync_dest), compose_cfg)
        stdout, stderr, rc = "", "", -1
        try:
            stdout, stderr, rc = rx_subprocess(docker_cmd, cwd=str(local_compose_dir), check=True)
        except subprocess.CalledProcessError as e:
            stdout = e.stdout
            stderr = e.stderr
            rc = e.returncode
            raise
        finally:
            print(f"[compose][up] Command exited with code {rc}")
            print(f"[compose][up] STDOUT: {stdout}")
            print(f"[compose][up] STDERR: {stderr}")

    # remote deployment via SSH
    elif dscheme == "ssh":
        if ":" in dhostpath:
            raise ValueError(f"Destination URL must not contain a path. The path will be set to {remote_compose_dir}")

        rsync_dest = f"{dest}:{remote_compose_dir}"
        upload_directory_via_rsync(local_compose_dir, rsync_dest, ssh_cfg, ctx)

        # establish SSH connection
        client = get_ssh_client(dest, ssh_cfg)

        # run setup.sh if exists
        if ctx.dry_run:
            print(f"Dry run mode, skipping setup.sh execution on {dest}")
        else:
            run_remote_hook_script(client, remote_compose_dir, "setup.sh")

        # prepend remote compose dir to compose files
        compose_files = [str(Path(remote_compose_dir) / cf) for cf in compose_files]
        docker_cmd = build_compose_up_command(compose_files, project_dir=remote_compose_dir, compose_cfg=compose_cfg)
        stdout, stderr, rc = "", "", -1
        try:
            cmd_str = " ".join(docker_cmd)
            print(f"[compose][up]Running command on remote {dest}: {cmd_str}")
            stdout, stderr, rc = ssh_execute_command(client, cmd_str)
        except Exception as e:
            print(f"[compose][up] SSH command error: {e}")
            raise
        finally:
            print(f"[compose][up] Command exited with code {rc}")
            print(f"[compose][up] STDOUT: {stdout}")
            print(f"[compose][up] STDERR: {stderr}")

        return stdout, stderr, rc
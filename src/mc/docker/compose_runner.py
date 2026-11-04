import abc
import logging
import os
import subprocess
from pathlib import Path
from typing import Callable

import pydantic
from docker.constants import DEFAULT_TIMEOUT_SECONDS

from mc.util.subprocess_helper import rx_subprocess
from mc.util.subprocess_util import kwargs_to_cmdargs

logger = logging.getLogger(__name__)

class DockerComposeArgs(pydantic.BaseModel):
    timeout: int = DEFAULT_TIMEOUT_SECONDS

class DockerComposeUpArgs(pydantic.BaseModel):
    detach: bool = False
    build: bool = False
    force_recreate: bool = False
    remove_orphans: bool = False
    quiet_pull: bool = False # Pull without printing progress information
    no_color: bool = False # Produce monochrome output
    yes: bool = False # Assume "yes" as answer to all prompts and run non-interactively

class DockerComposeSyncArgs(pydantic.BaseModel):
    timeout: int = DEFAULT_TIMEOUT_SECONDS

class DockerComposeStopArgs(pydantic.BaseModel):
    timeout: int = DEFAULT_TIMEOUT_SECONDS

class DockerComposeDownArgs(pydantic.BaseModel):
    timeout: int = DEFAULT_TIMEOUT_SECONDS


def default_cmd_executor(cmd: list[str], env: dict[str, str] | None = None) -> tuple[bytes, bytes, int]:
    try:
        logger.info(f"COMPOSE CMD: {' '.join(cmd)}")
        p1 = subprocess.run(cmd, cwd=None, env=env, capture_output=True, check=True)
        logger.info("COMPOSE STDOUT", p1.stdout)
        logger.info("COMPOSE STDERR", p1.stderr)

        return p1.stdout, p1.stderr, p1.returncode
    except subprocess.CalledProcessError as e:
        logger.exception("COMPOSE PROCESS ERROR", exc_info=True)
        raise RuntimeError(
            f"Compose command failed with exit code {e.returncode}: {e.stderr.decode('utf-8')}"
        ) from e
    except Exception as e:
        logger.info("COMPOSE ERROR", exc_info=True)
        raise e


class DockerComposeStackRunner(abc.ABC):
    def __init__(self, project_name, executor: Callable | None = None):
        self.project_name = project_name
        self.executor = executor or default_cmd_executor

    @abc.abstractmethod
    def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
        raise NotImplementedError("_compose method must be implemented by subclasses")

    @abc.abstractmethod
    def sync(self, args: DockerComposeSyncArgs) -> tuple[bytes, bytes, int]:
        """
        Sync the stack files to the target.
        Override in subclasses to implement the sync method.
        """
        raise NotImplementedError("sync method must be implemented by subclasses")

    def up(self, args: DockerComposeUpArgs) -> tuple[bytes, bytes, int]:
        """
        Start the stack
        https://docs.docker.com/reference/cli/docker/compose/up/
        """
        logger.info(f"Starting project {self.project_name}")

        #kwargs = args.model_dump(mode='python')
        kwargs = dict()
        kwargs["detach"] = args.detach
        kwargs["build"] = args.build
        kwargs["force_recreate"] = args.force_recreate
        kwargs["remove_orphans"] = args.remove_orphans
        kwargs["quiet_pull"] = args.quiet_pull
        kwargs["no_color"] = args.no_color
        kwargs["yes"] = args.yes

        return self._compose("up", **kwargs)

    def down(self, args: DockerComposeDownArgs) -> tuple[bytes, bytes, int]:
        """
        Remove the stack
        https://docs.docker.com/reference/cli/docker/compose/down/
        """
        logger.info(f"COMPOSE DOWN {self.project_name}")
        kwargs = args.model_dump(mode="python")
        return self._compose("down", **kwargs)

    def stop(self, args: DockerComposeStopArgs) -> tuple[bytes, bytes, int]:
        """
        Stop the stack
        https://docs.docker.com/reference/cli/docker/compose/stop/
        """
        logger.info(f"COMPOSE STOP {self.project_name}")
        kwargs = args.model_dump(mode="python")
        return self._compose("stop", **kwargs)

    def restart(self, args: DockerComposeArgs) -> tuple[bytes, bytes, int]:
        """
        Restart the stack.
        https://docs.docker.com/reference/cli/docker/compose/restart/
        """
        logger.info(f"COMPOSE RESTART {self.project_name}")
        kwargs = args.model_dump(mode="python")
        return self._compose("restart", **kwargs)

    def delete(self, args: DockerComposeArgs) -> tuple[bytes, bytes, int]:
        """
        Deletes the stack resources.

        !Not an official docker compose command!
        This cleans up any resources associated with the stack.
        Removes the project directory.
        """
        logger.info(f"COMPOSE DELETE {self.project_name}")
        # kwargs = args.model_dump(mode="python")
        # return b"COMPOSE DESTROY: No docker-specific destroy actions executed."
        raise NotImplementedError("Delete method must be implemented by subclasses")

    def ps(self, args: DockerComposeArgs) -> tuple[bytes, bytes, int]:
        """
        Get the status of the stack.
        https://docs.docker.com/compose/reference/ps/

        Same as `docker compose ps`
        """
        kwargs = args.model_dump(mode="python")
        return self._compose("ps", **kwargs)


class LocalDockerComposeStackRunner(DockerComposeStackRunner):
    """
    Docker Compose container stack.

    This class is used to manage the lifecycle of a Docker Compose stack
    """

    def __init__(
        self,
        project_name: str,
        local_dir: str,
        docker_host: str="unix:///var/run/docker.sock",
        stackfiles: str | list = "compose.yaml",
        executor: Callable | None = None,
    ):
        super().__init__(project_name, executor=executor)
        self.docker_host = docker_host
        self.project_name = project_name
        self.project_dir = local_dir # real project dir. in docker environments, this is the host path!
        if isinstance(stackfiles, str):
            stackfiles = [stackfiles]
        self.stackfiles = stackfiles


    def up(self, args: DockerComposeUpArgs) -> tuple[bytes, bytes, int]:
        # run setup.sh if exists
        #run_local_hook_script(Path(self.project_dir), "setup.sh")
        return super().up(args)

    def sync(self, args: DockerComposeSyncArgs) -> tuple[bytes, bytes, int]:
        """
        Sync the stack files to the target
        """
        return b"", b"", 0

    def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Run a docker compose command locally

        :param cmd: Command to run
        :param kwargs: Additional arguments to pass to docker compose
        :return:
        """
        project_dir = self.project_dir # real project dir path!

        env = os.environ.copy()
        env["DOCKER_HOST"] = self.docker_host
        env["COMPOSE_PROJECT_DIRECTORY"] = project_dir
        env["COMPOSE_PROJECT_NAME"] = self.project_name

        _cmd = ["docker", "compose"]
        _cmd.extend(["--project-directory", project_dir])
        # _cmd.extend(["--project-name", self.project_name])
        for cf in self.stackfiles:
            _cmd.extend(["--file", cf])
        _cmd.append(cmd)  # up/down/etc.
        _cmd.extend(kwargs_to_cmdargs(kwargs))

        return self.executor(cmd=_cmd, env=env)


def run_local_hook_script(local_compose_dir: Path, script_name: str) -> tuple[bytes, bytes, int]:
    stdout, stderr, rc = b"", b"", 0  # default success
    setup_script = local_compose_dir / script_name
    if setup_script.exists() and setup_script.is_file():
        logger.info(f"Found setup.sh script at {setup_script}, executing on remote host...")
        cmd_str = "chmod +x setup.sh && ./setup.sh"
        logger.info(f"Hook command: {cmd_str}")
        try:
            stdout, stderr, rc = rx_subprocess(cmd_str, cwd=str(local_compose_dir), shell=True)
        except subprocess.CalledProcessError as e:
            stdout = e.stdout
            stderr = e.stderr
            rc = e.returncode

        if rc != 0:
            raise RuntimeError(f"{script_name} failed with exit code {rc}")

        logger.info(f"Local Hook script {script_name} exited with code {rc}")
        logger.info(f"Local Hook script {script_name} STDOUT: {stdout}")
        logger.info(f"Local Hook script {script_name} STDERR: {stderr}")
    return stdout, stderr, rc



# class RemoteDockerComposeStackRunner(DockerComposeStackRunner):
#     """
#     Docker Compose stack runner for remote Docker hosts.
#     """
#
#     def __init__(
#         self,
#         project_name: str,
#         local_dir: str,
#         docker_host: str,
#         stackfile: str | list = None,
#         ssh_config: dict = None,
#         **kwargs,
#     ):
#         super().__init__(project_name)
#         self.local_dir = local_dir
#         self.remote_dir = f"~/.compose/{self.project_name}"
#         self.docker_host = docker_host
#         if not stackfile:
#             stackfile = ["compose.yaml"]
#         if isinstance(stackfile, str):
#             stackfile = [stackfile]
#         self.stackfile = stackfile
#         self.ssh_config = ssh_config if ssh_config is not None else {}
#         self._ssh_client = None
#
#     @property
#     def ssh_client(self):
#         if self._ssh_client is None:
#             self._ssh_client = get_ssh_client(self.docker_host, self.ssh_config)
#         return self._ssh_client
#
#     def sync(self, **kwargs) -> tuple[bytes, bytes, int]:
#         """
#         Sync the local compose project directory to the remote docker host.
#         """
#         rsync_dest = f"{self.docker_host}:{self.remote_dir}"
#         return rsync_execute(src=self.local_dir, dest=rsync_dest, mkdir=True, delete=True, ssh_config=self.ssh_config)
#
#     def up(self, **kwargs) -> tuple[bytes, bytes, int]:
#         # run setup.sh if exists
#         if Path(self.local_dir).is_dir() and (Path(self.local_dir) / "setup.sh").exists():
#             stdout, stderr, rc = run_remote_hook_script(self.ssh_client, self.remote_dir, "setup.sh")
#             if rc != 0:
#                 raise RuntimeError(f"Remote setup.sh failed with exit code {rc}")
#
#         return super().up(**kwargs)
#
#     def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
#         """
#         Run a docker compose command on the remote docker host.
#
#         :param cmd: Command to run
#         :param kwargs: Additional arguments to pass to docker compose
#         :return: (stdout, stderr, returncode)
#         """
#         remote_working_dir = self.remote_dir
#         # compose_project_name = self.project_name
#         try:
#             _composecmd = ["docker", "compose", "--project-directory", remote_working_dir]
#             for cf in self.stackfile:
#                 _composecmd.append("--file")
#                 _composecmd.append(remote_working_dir + "/" + cf)
#             pcmd = _composecmd + [cmd] + kwargs_to_cmdargs(kwargs)
#             logger.info(f"[rcompose] RAW CMD: {pcmd}")
#
#             # add override compose files from remote dir
#
#             # environment variables for docker compose ON THE REMOTE HOST (!)
#             renv = dict()
#             # renv['PATH'] = os.getenv('PATH')
#             # _todo renv['DOCKER_HOST'] = 'unix:///var/run/docker.sock' # the docker host on the REMOTE machine
#             # renv['DOCKER_HOST'] = 'unix:///var/run/docker.sock'
#             renv["COMPOSE_PROJECT_DIRECTORY"] = remote_working_dir
#             # renv['COMPOSE_PROJECT_NAME'] = compose_project_name
#             # renv['COMPOSE_FILE'] = compose_file_name
#             # renv['PWD'] = remote_working_dir
#
#             # prepend remote compose dir to compose files
#             # compose_files = [str(Path(remote_compose_dir) / cf) for cf in compose_files]
#             stdout, stderr, rc = b"", b"", -1
#             try:
#                 # cmd_str = f"cd {remote_working_dir} && " + " ".join(pcmd)
#                 cmd_str = " ".join(pcmd)
#                 logger.info(f"[rcompose] [{self.docker_host}] Executing command: {cmd_str}")
#                 stdout, stderr, rc = ssh_execute_command(self.ssh_client, cmd_str, environment=renv)
#             except Exception as e:
#                 logger.exception(f"[rcompose] SSH command error: {e}", exc_info=True)
#                 raise
#             finally:
#                 logger.info(f"[rcompose] Command exited with code {rc}")
#                 logger.info(f"[rcompose] STDOUT: {stdout}")
#                 logger.info(f"[rcompose] STDERR: {stderr}")
#             return stdout, stderr, rc
#         except Exception as e:
#             logger.exception(f"[rcompose] Error running compose command on remote host: {e}", exc_info=True)
#             raise e



# def get_ssh_client(dest, ssh_cfg: dict) -> SSHClient:
#     ssh_params = ssh_params_from_url(dest, ssh_params=ssh_cfg, use_ssh_config=False)
#     logger.info(f"SSH params: {ssh_params}")
#
#     ssh_hostname = ssh_params.get("hostname")
#     ssh_port = ssh_params.get("port")
#     ssh_user = ssh_params.get("username")
#     # ssh_password = ssh_params.get("password")
#     # ssh_key_file = ssh_params.get("key_filename")
#     # ssh_key_pass = ssh_params.get("key_passphrase")
#     try:
#         client = ssh_connect(
#             hostname=ssh_hostname,
#             port=ssh_port,
#             username=ssh_user,
#         )
#         # password=ssh_password, key_filename=ssh_key_file, key_passphrase=ssh_key_pass)
#         if not client:
#             raise ConnectionError(f"SSH client failed to connect to {dest}")
#         logger.info(f"SSH client connected to {dest}")
#         return client
#     except Exception as e:
#         # print stack trace
#         import traceback
#
#         traceback.print_exc()
#
#         logger.info(f"SSH client connection error: {e}")
#         raise

# def run_remote_hook_script(client: SSHClient, remote_compose_dir: str, script_name: str) -> tuple[bytes, bytes, int]:
#     stdout, stderr, rc = "", "", 0  # default success
#     try:
#         cmd_str = f"cd {remote_compose_dir} && chmod +x {script_name} && bash ./{script_name}"
#         logger.info(f"Remote Hook command: {cmd_str}")
#         stdout, stderr, rc = ssh_execute_command(client, cmd_str)
#         logger.info(f"{script_name} exited with code {rc}")
#         # if rc != 0:
#         #    raise RuntimeError(f"Remote hook script {script_name} failed with exit code {rc}")
#     except Exception as e:
#         logger.info(f"SSH remote execution error: {e}")
#         stdout = ""
#         stderr = str(e)
#         rc = -1
#         raise
#     finally:
#         logger.info(f"Remote Hook script {script_name} exited with code {rc}")
#         logger.info(f"Remote Hook script {script_name} STDOUT: {stdout}")
#         logger.info(f"Remote Hook script {script_name} STDERR: {stderr}")
#     return stdout, stderr, rc
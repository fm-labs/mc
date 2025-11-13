import abc
import os
import subprocess

from docker.constants import DEFAULT_TIMEOUT_SECONDS
from paramiko.client import SSHClient

from mc.util.subprocess_util import kwargs_to_cmdargs
from rx.helper.rsync_helper import rsync_execute
from rx.helper.sshpy_helper import ssh_execute_command, ssh_params_from_url, ssh_connect


class DockerComposeStackRunner(abc.ABC):

    def __init__(self, project_name):
        self.project_name = project_name

    @abc.abstractmethod
    def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
        raise NotImplementedError("_compose method must be implemented by subclasses")

    def sync(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Sync the stack files to the target
        Override in subclasses if needed
        """
        pass

    def up(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Start the stack
        https://docs.docker.com/reference/cli/docker/compose/up/
        """
        print(f"Starting project {self.project_name}")

        kwargs['detach'] = True if 'detach' not in kwargs else kwargs['detach']
        kwargs['build'] = True if 'build' not in kwargs else kwargs['build']
        kwargs['force-recreate'] = True if 'force-recreate' not in kwargs else kwargs['force-recreate']
        # kwargs['y'] = True if 'y' not in kwargs else kwargs['y'] # run non-interactively
        return self._compose("up", **kwargs)

    def down(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Remove the stack
        https://docs.docker.com/reference/cli/docker/compose/down/
        """
        print(f"COMPOSE DOWN {self.project_name}")

        kwargs['timeout'] = DEFAULT_TIMEOUT_SECONDS if 'timeout' not in kwargs else kwargs['timeout']
        return self._compose("down", **kwargs)

    def stop(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Stop the stack
        https://docs.docker.com/reference/cli/docker/compose/stop/
        """
        print(f"COMPOSE STOP {self.project_name}")

        kwargs['timeout'] = DEFAULT_TIMEOUT_SECONDS if 'timeout' not in kwargs else kwargs['timeout']
        return self._compose("stop", **kwargs)

    def restart(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Restart the stack.
        """
        print(f"COMPOSE RESTART {self.project_name}")

        # Run docker compose restart
        kwargs['timeout'] = DEFAULT_TIMEOUT_SECONDS if 'timeout' not in kwargs else kwargs['timeout']
        return self._compose("restart", **kwargs)

    def delete(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Deletes the stack resources.

        !Not a docker compose command!
        This cleans up any resources associated with the stack.
        Removes the project directory.
        """
        print(f"COMPOSE DELETE {self.project_name}")
        #return b"COMPOSE DESTROY: No docker-specific destroy actions executed."
        raise NotImplementedError("Delete method must be implemented by subclasses")

    def ps(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Get the status of the stack

        Same as `docker compose ps`
        """
        return self._compose("ps", **kwargs)


class LocalDockerComposeStackRunner(DockerComposeStackRunner):
    """
    Docker Compose container stack.

    This class is used to manage the lifecycle of a Docker Compose stack
    """

    def __init__(self, project_name, local_dir, docker_host="unix:///var/run/docker.sock", **kwargs):
        super().__init__(project_name)
        self.project_name = project_name
        self.local_dir = local_dir
        self.docker_host = docker_host


    def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Run a docker compose command locally

        :param cmd: Command to run
        :param kwargs: Additional arguments to pass to docker compose
        :return:
        """
        working_dir = self.local_dir
        if working_dir is None or not os.path.isdir(working_dir):
            raise Exception(f"Invalid working directory: {working_dir}")

        compose_file = 'docker-compose.yml'
        if os.path.exists(os.path.join(working_dir, 'docker-compose.stack.yml')):
            compose_file = 'docker-compose.stack.yml'

        compose_args = dict()
        compose_args['project-name'] = self.project_name
        compose_args['project-directory'] = working_dir
        compose_args['file'] = compose_file
        compose_args['progress'] = 'plain'
        try:
            pcmd = ((["docker-compose"]
                     + kwargs_to_cmdargs(compose_args))  # compose specific args
                    + [cmd]  # the compose command (up/down/...)
                    + kwargs_to_cmdargs(kwargs))  # additional command args
            print(f"RAW CMD: {pcmd}")
            print(f"CMD: {' '.join(pcmd)}")

            penv = os.environ.copy()
            penv['DOCKER_HOST'] = self.docker_host
            #penv['DOCKER_CONFIG'] = settings.DOCKER_CONFIG
            penv['COMPOSE_PROJECT_DIRECTORY'] = working_dir
            penv['COMPOSE_PROJECT_NAME'] = self.project_name
            penv['COMPOSE_FILE'] = compose_file
            penv['PWD'] = working_dir

            p1 = subprocess.run(pcmd, cwd=working_dir, env=penv, capture_output=True, check=True)
            print("STDOUT", p1.stdout)
            print("STDERR", p1.stderr)

            return p1.stdout, p1.stderr, p1.returncode
        except Exception as e:
            print("COMPOSE RUN ERROR", str(e))
            raise e


def get_ssh_client(dest, ssh_cfg: dict) -> SSHClient:
    ssh_params = ssh_params_from_url(dest, ssh_params=ssh_cfg, use_ssh_config=False)
    print(f"SSH params: {ssh_params}")

    ssh_hostname = ssh_params.get("hostname")
    ssh_port = ssh_params.get("port")
    ssh_user = ssh_params.get("username")
    ssh_password = ssh_params.get("password")
    ssh_key_file = ssh_params.get("key_filename")
    ssh_key_pass = ssh_params.get("key_passphrase")
    try:
        client = ssh_connect(hostname=ssh_hostname, port=ssh_port,
                             username=ssh_user, password=ssh_password,
                             key_filename=ssh_key_file, key_passphrase=ssh_key_pass)
        if not client:
            raise ConnectionError(f"SSH client failed to connect to {dest}")
        print(f"SSH client connected to {dest}")
        return client
    except Exception as e:
        # print stack trace
        import traceback
        traceback.print_exc()

        print(f"SSH client connection error: {e}")
        raise

class RemoteDockerComposeStackRunner(LocalDockerComposeStackRunner):
    """
    Docker Compose stack runner for remote Docker hosts.
    """

    def __init__(self, project_name: str, local_dir: str, docker_host: str, ssh_config: dict = None, **kwargs):
        super().__init__(project_name, local_dir=local_dir, docker_host=docker_host, **kwargs)
        self.remote_dir = f"~/.compose/{self.project_name}"
        self.docker_host = docker_host
        self.ssh_config = ssh_config if ssh_config is not None else {}
        self.ssh_client = None

    def _connect_ssh(self):
        if self.ssh_client is None:
            self.ssh_client = get_ssh_client(self.docker_host, self.ssh_config)
        return self.ssh_client

    def sync(self, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Sync the local compose project directory to the remote docker host.
        """
        rsync_dest = f"{self.docker_host}:{self.remote_dir}"
        return rsync_execute(src=self.local_dir, dest=rsync_dest, mkdir=True, ssh_config=self.ssh_config)

    def up(self, **kwargs) -> bytes:
        #cmd = ["up", "-d", "--remove-orphans", "--force-recreate"]

        # run setup.sh if exists
        run_remote_hook_script(self.ssh_client, self.remote_dir, "setup.sh")

        return super().up(**kwargs)

    def _compose(self, cmd, **kwargs) -> tuple[bytes, bytes, int]:
        """
        Run a docker compose command on the remote docker host.

        :param cmd: Command to run
        :param kwargs: Additional arguments to pass to docker compose
        :return: (stdout, stderr, returncode)
        """
        remote_working_dir = self.remote_dir
        compose_project_name = self.project_name
        compose_file_name = 'compose.yaml'

        compose_args = dict()
        compose_args['project-name'] = self.project_name
        compose_args['project-directory'] = remote_working_dir
        compose_args['file'] = compose_file_name
        compose_args['progress'] = 'plain'
        try:
            pcmd = ((["docker-compose"]
                     + kwargs_to_cmdargs(compose_args))  # compose specific args
                    + [cmd]  # the compose command (up/down/...)
                    + kwargs_to_cmdargs(kwargs))  # additional command args
            print(f"RAW CMD: {pcmd}")
            print(f"CMD: {' '.join(pcmd)}")

            # environment variables for docker compose ON THE REMOTE HOST (!)
            renv = dict()
            # renv['PATH'] = os.getenv('PATH')
            # todo renv['DOCKER_HOST'] = 'unix:///var/run/docker.sock' # the docker host on the remote machine
            # todo renv['DOCKER_CONFIG'] = settings.DOCKER_CONFIG # the docker config on the remote machine
            #renv['DOCKER_HOST'] = 'unix:///var/run/docker.sock'
            renv['COMPOSE_PROJECT_DIRECTORY'] = remote_working_dir
            renv['COMPOSfE_PROJECT_NAME'] = compose_project_name
            renv['COMPOSE_FILE'] = compose_file_name
            renv['PWD'] = remote_working_dir

            # establish SSH connection
            client = get_ssh_client(self.docker_host, self.ssh_config)


            # prepend remote compose dir to compose files
            #compose_files = [str(Path(remote_compose_dir) / cf) for cf in compose_files]
            stdout, stderr, rc = "", "", -1
            try:
                cmd_str = " ".join(cmd)
                print(f"[rcompose] [{self.docker_host}] Executing command: {cmd_str}")
                stdout, stderr, rc = ssh_execute_command(client, cmd_str)
            except Exception as e:
                print(f"[rcompose] SSH command error: {e}")
                raise
            finally:
                print(f"[rcompose] Command exited with code {rc}")
                print(f"[rcompose] STDOUT: {stdout}")
                print(f"[rcompose] STDERR: {stderr}")

            return stdout, stderr, rc


        except Exception as e:
            print(e)
            raise e


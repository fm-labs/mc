import os
import logging

from mc import logs
from mc.docker.compose_runner import LocalDockerComposeStackRunner, RemoteDockerComposeStackRunner
from mc.util.gitcli_util import git_update, git_clone

logger = logging.getLogger(__name__)
logger.addHandler(logs.get_rotating_file_log_handler("tasks"))

#@celery.task(bind=True)
def clone_or_update_git_repo(repo_url: str, checkout_dir: str, private_key_file=None) -> dict:

    stdout, stderr, rc = "", "", -1
    msg = ""
    if not os.path.exists(checkout_dir) or not os.path.isdir(checkout_dir):
        # Clone the repository
        logger.info(f"Git repo {repo_url} does not exist at {checkout_dir}. Cloning...")
        try:
            # git.Repo.clone_from(repo_url, stack.project_dir)
            stdoutb, stderrb, rc = git_clone(repo_url,
                                             checkout_dir,
                                             private_key_file=private_key_file)
            stdout = stdoutb.decode('utf-8') if stdoutb else ''
            stderr = stderrb.decode('utf-8') if stderrb else ''

            logger.info("Git clone stdout: %s", stdout)
            logger.error("Git clone stderr: %s", stderr)
            #print(stdout)
            #print(stderr)
            msg = f"🚀 Git repo {repo_url} cloned to: {checkout_dir}"
            logger.info(msg)
        except Exception as e:
            logger.exception(f"Error cloning repository from {repo_url} to {checkout_dir}: {e}", exc_info=True)
            raise ValueError(f"Error cloning repository: {e}")

    else:
        # check if .git exists
        git_dir = os.path.join(checkout_dir, ".git")
        if not os.path.exists(git_dir) or not os.path.isdir(git_dir):
            raise ValueError(f"Directory '{checkout_dir}' exists but is not a git repository")

        logger.info(f"Git repo already exists at {checkout_dir}. Pulling latest changes from {repo_url}...")
        # Pull the latest changes
        # try:
        #     repo = git.Repo(app_dir)
        #     origin = repo.remotes.origin
        #     origin.pull()
        #     print(f"Repository at {app_dir} updated successfully.")
        # except Exception as e:
        #     raise ValueError(f"Error updating repository: {e}")
        try:
            # git.Repo.clone_from(repo_url, stack.project_dir)
            stdoutb, stderrb, rc = git_update(checkout_dir,
                                              private_key_file=private_key_file)
            stdout = stdoutb.decode('utf-8') if stdoutb else ''
            stderr = stderrb.decode('utf-8') if stderrb else ''
            msg = f"🚀 Git repo {repo_url} updated in: {checkout_dir}"
            logger.info(msg)
        except Exception as e:
            logger.exception(f"Error updating repository at {checkout_dir}: {e}", exc_info=True)
            raise ValueError(f"Error cloning repository: {e}")

    return {"status": "success", "app_dir": checkout_dir, "stdout": stdout, "stderr": stderr, "return_code": rc}


#@celery.task(bind=True)
def task_deploy_compose_project(project_name: str, project_dir: str, stackfile: str | list, host_url: str, **kwargs) -> dict:
    """
    Deploy a Docker Compose project to a specified host.

    :param project_name: The name of the project (used as the Docker Compose project name).
    :param project_dir: The local directory containing the Docker Compose stack file.
    :param stackfile: The path to the Docker Compose stack file (can be a single file or a list of files).
    :param host_url: The URL of the Docker host to deploy to (e.g., "unix:///var/run/docker.sock" for local, "ssh://user@remotehost" for remote).
    :param kwargs: Additional keyword arguments for the Docker Compose up command (e.g., build, remove_orphans, force_recreate).
    :return: A dictionary containing the status, message, and output of the deployment process.
    """
    if host_url.startswith("unix://"):
        compose_runner = LocalDockerComposeStackRunner(
            project_name=project_name,
            local_dir=project_dir,
            stackfile=stackfile,
            docker_host=host_url
        )
    elif host_url.startswith("ssh://"):
        compose_runner = RemoteDockerComposeStackRunner(
            project_name=project_name,
            local_dir=project_dir,
            stackfile=stackfile,
            docker_host=host_url
        )
    else:
        raise ValueError(f"Unsupported host URL scheme: {host_url}")

    compose_runner.stop()
    compose_runner.sync()

    up_args = {
        "detach": True, # always detach!
        "build": kwargs.get("build", False),
        "remove_orphans": kwargs.get("remove_orphans", False),
        "force_recreate": kwargs.get("force_recreate", False),
        #"quiet_pull": kwargs.get("quiet_pull", True),
        #"yes": kwargs.get("yes", True),
    }
    stdout, stderr, rc = compose_runner.up(**up_args)
    return {"status": "success",
            "message": f"App {project_name} deployed to {host_url}",
            "stdout": stdout.decode(), "stderr": stderr.decode(), "return_code": rc}

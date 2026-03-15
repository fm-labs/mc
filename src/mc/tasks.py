import os

from mc.docker.compose_runner import LocalDockerComposeStackRunner, RemoteDockerComposeStackRunner
from mc.util.gitcli_util import git_update, git_clone
from orchestra.celery import celery


@celery.task(bind=True)
def clone_or_update_git_repo(self, repo_url: str, checkout_dir: str, private_key_file=None) -> dict:

    stdout, stderr, rc = "", "", -1
    msg = ""
    if not os.path.exists(checkout_dir) or not os.path.isdir(checkout_dir):
        # Clone the repository
        try:
            # git.Repo.clone_from(repo_url, stack.project_dir)
            stdoutb, stderrb, rc = git_clone(repo_url,
                                             checkout_dir,
                                             private_key_file=private_key_file)
            stdout = stdoutb.decode('utf-8') if stdoutb else ''
            stderr = stderrb.decode('utf-8') if stderrb else ''
            #print(stdout)
            #print(stderr)
            msg = f"🚀 Git repo {repo_url} cloned to: {checkout_dir}"
            print(msg)
        except Exception as e:
            raise ValueError(f"Error cloning repository: {e}")

    else:
        # check if .git exists
        git_dir = os.path.join(checkout_dir, ".git")
        if not os.path.exists(git_dir) or not os.path.isdir(git_dir):
            raise ValueError(f"Directory '{checkout_dir}' exists but is not a git repository")

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
            print(msg)
        except Exception as e:
            raise ValueError(f"Error cloning repository: {e}")

    return {"status": "success", "app_dir": checkout_dir, "stdout": stdout, "stderr": stderr, "return_code": rc}


@celery.task(bind=True)
def task_deploy_compose_stack(self, project_name: str, project_dir: str, stackfile: str|list, host_url: str):
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

    stdout, stderr, rc = compose_runner.up()
    return {"status": "success",
            "message": f"App {project_name} deployed to {host_url}",
            "stdout": stdout.decode(), "stderr": stderr.decode(), "return_code": rc}

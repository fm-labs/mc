import os

from mc.util.gitcli_util import git_update, git_clone
from orchestra.celery import celery


@celery.task(bind=True)
def update_project_from_git(self, source_url: str, app_dir: str, private_key_file=None) -> dict:

    stdout, stderr, rc = "", "", -1
    msg = ""
    if not os.path.exists(app_dir) or not os.path.isdir(app_dir):
        # Clone the repository
        try:
            # git.Repo.clone_from(repo_url, stack.project_dir)
            stdoutb, stderrb, rc = git_clone(source_url,
                               app_dir,
                               private_key_file=private_key_file)
            stdout = stdoutb.decode('utf-8') if stdoutb else ''
            stderr = stderrb.decode('utf-8') if stderrb else ''
            #print(stdout)
            #print(stderr)
            msg = f"🚀 Git repo {source_url} cloned to: {app_dir}"
            print(msg)
        except Exception as e:
            raise ValueError(f"Error cloning repository: {e}")

    else:
        # check if .git exists
        git_dir = os.path.join(app_dir, ".git")
        if not os.path.exists(git_dir) or not os.path.isdir(git_dir):
            raise ValueError(f"Directory '{app_dir}' exists but is not a git repository")

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
            stdoutb, stderrb, rc = git_update(app_dir,
                               private_key_file=private_key_file)
            stdout = stdoutb.decode('utf-8') if stdoutb else ''
            stderr = stderrb.decode('utf-8') if stderrb else ''
            msg = f"🚀 Git repo {source_url} updated in: {app_dir}"
            print(msg)
        except Exception as e:
            raise ValueError(f"Error cloning repository: {e}")

    return {"status": "success", "app_dir": app_dir, "stdout": stdout, "stderr": stderr, "return_code": rc}
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests
import git  # Requires GitPython package

from mc.config import DATA_DIR


def get_app_stack_dir(stack_name: str) -> str:
    return str(DATA_DIR / "apps" / stack_name)


def create_app_stack(stack_name: str, src: str, stackfile: str, **kwargs) -> dict:
    """
    Create a Docker Compose application from various sources.
    Invokes the appropriate function based on the src scheme.

    # src url schemes:
    # - file://path/to/local/template
    # - git://user/repo.git
    # - git://user/repo.git#branch
    # - https://github.com/user/repo.git#branch
    # - https://example.com/path/to/template.zip (zip or tar.gz)
    """
    app_dir = get_app_stack_dir(stack_name)

    item = {
        "stack_name": stack_name,
        "template_stackfile": stackfile,
    }

    if src.startswith("file://"):
        template_dir = src[len("file://"):]
        _item = create_app_stack_from_template_dir(stack_name, app_dir, template_dir)
        item.update(_item)

    elif src.startswith("git://") or (src.startswith("https://") and src.endswith(".git")):
        scheme, url_part = src.split("://", 1)
        if '#' in url_part:
            repo_part, branch = src.split('#', 1)
        else:
            repo_part = url_part
            branch = "main"

        _item = create_app_stack_from_git_repo(stack_name, app_dir, repo_part, branch)
        item.update(_item)

    elif src.startswith("https://") and (src.endswith(".zip") or src.endswith(".tar.gz") or src.endswith(".tgz")):
        template_url = src
        _item = create_app_stack_from_url_template(stack_name, app_dir, template_url)
        item.update(_item)
    else:
        raise ValueError(f"Unsupported source URL scheme: {src}")
    return item


def create_app_stack_from_template_dir(stack_name: str, app_dir: str, template_dir: str) -> dict:
    """
    Create a Docker Compose application from a local template directory.

    Args:
        stack_name (str): Name of the application.
        app_dir (str): Directory where the application will be created.
        template_dir (str): Path to the local template directory.
    """
    app_path = Path(app_dir)
    if app_path.exists():
        raise FileExistsError(f"Application directory already exists: {app_dir}")

    shutil.copytree(template_dir, app_path)
    print(f"Created application '{stack_name}' from template directory '{template_dir}' at '{app_dir}'")

    return {
        "template_repository": f"file://{template_dir}",
    }


def create_app_stack_from_git_repo(stack_name: str, app_dir: str, git_repo: str, git_branch: str = None) -> dict:
    """
    Create a Docker Compose application by cloning a git repository.

    Args:
        stack_name (str): Name of the application.
        app_dir (str): Directory where the application will be created.
        git_repo (str): GitHub repository in the format "user/repo".
        git_branch (str): Branch to clone. Default is "main".
    """

    app_path = Path(app_dir)
    if app_path.exists():
        raise FileExistsError(f"Application directory already exists: {app_dir}")

    repo_url = git_repo
    print(f"Cloning repository '{repo_url}' into '{app_dir}'")
    git.Repo.clone_from(repo_url, app_path, branch=git_branch)
    print(f"Cloned repository '{git_repo}' (branch: {git_branch}) into '{app_dir}'")


    return {
        "template_repository": f"{git_repo}#{git_branch}" if git_branch else git_repo,
    }


# def create_app_stack_from_git_repo_template(stack_name: str, app_dir: str,
#                                               template_git_repo: str,
#                                               template_git_branch: str = "main",
#                                               template_folder: str = "") -> dict:
#     """
#     Create a Docker Compose application from a template stored in a git repository.
#
#     Args:
#         stack_name (str): Name of the application.
#         app_dir (str): Directory where the application will be created.
#         template_git_repo (str): GitHub repository containing templates in the format "user/repo".
#         template_git_branch (str): Branch to clone. Default is "main".
#         template_folder (str): Name of the template folder inside the repo. Default is "basic".
#     """
#     app_path = Path(app_dir)
#     if app_path.exists():
#         raise FileExistsError(f"Application directory already exists: {app_dir}")
#
#
#     with tempfile.TemporaryDirectory() as tmpdir:
#         repo_url = template_git_repo
#         git.Repo.clone_from(repo_url, tmpdir, branch=template_git_branch)
#         template_path = Path(tmpdir) / template_folder
#         if not template_path.exists():
#             raise FileNotFoundError(f"Template '{template_folder}' not found in repository '{template_git_repo}'")
#         shutil.copytree(template_path, app_path)
#         print(
#             f"Created application '{stack_name}' from template '{template_folder}' in repo '{template_git_repo}' at '{app_dir}'")
#
#     return {
#         "template_url": f"git-template://{template_git_repo}#{template_git_branch}/{template_folder}".rstrip("/"),
#         "template_git_repo": template_git_repo,
#         "template_git_branch": template_git_branch,
#         "template_dir": template_folder,
#     }


def create_app_stack_from_url_template(stack_name: str, app_dir: str, template_url: str) -> dict:
    """
    Create a Docker Compose application by downloading a template from a URL (zip or tar.gz).

    Args:
        stack_name (str): Name of the application.
        app_dir (str): Directory where the application will be created.
        template_url (str): URL to the zip or tar.gz archive containing the template.
    """

    app_path = Path(app_dir)
    if app_path.exists():
        raise FileExistsError(f"Application directory already exists: {app_dir}")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "template_archive"

        # Download the archive
        response = requests.get(template_url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download template from {template_url}: Status code {response.status_code}")

        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extract the archive
        if template_url.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
        elif template_url.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(tmpdir)
        else:
            raise ValueError("Unsupported archive format. Only .zip and .tar.gz are supported.")

        # Assume the contents are at the root of the extracted folder
        extracted_items = list(Path(tmpdir).iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            shutil.copytree(extracted_items[0], app_path)
        else:
            shutil.copytree(Path(tmpdir), app_path)

        print(f"Created application '{stack_name}' from URL template '{template_url}' at '{app_dir}'")

    return {
        "template_repository": template_url,
    }

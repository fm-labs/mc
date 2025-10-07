import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import field, dataclass
from pathlib import Path

import requests
import git  # Requires GitPython package

COMPOSE_APP_BASE_DIR = Path("data/projects")
#COMPOSE_APP_TEMPLATES_DIR = Path("resources/compose-templates")

@dataclass
class ComposeApp:
    name: str
    project: str
    source: str  # e.g., file://, git://, https://, git-template://
    properties: dict = field(default_factory=dict)



def get_compose_app_dir(app_name: str, project_name: str) -> str:
    return str(COMPOSE_APP_BASE_DIR / project_name / "apps" / app_name)


def create_compose_app(src: str, app_name: str, project_name: str, **kwargs) -> dict:
    """
    Create a Docker Compose application from various sources.
    Invokes the appropriate function based on the src scheme.

    # unified compose app src url scheme:
    # - file://path/to/local/template
    # - git://user/repo.git#branch
    # - https://example.com/path/to/repo.git#branch
    # - git-template://user/repo.git#branch/template-name
    # - https://example.com/path/to/template.zip (zip or tar.gz)
    """
    app_dir = get_compose_app_dir(app_name, project_name)

    item = {
        "app_name": app_name,
        "project_name": project_name,
        #"source_url": src,
    }

    if src.startswith("file://"):
        template_dir = src[len("file://"):]
        _item = create_compose_app_from_template_dir(app_name, app_dir, template_dir)
        item.update(_item)

    elif src.startswith("git-template://"):
        remainder = src[len("git-template://"):]
        if '#' in remainder:
            repo_part, template_name = remainder.split('#', 1)
            if '/' in template_name:
                branch, template_name = template_name.split('/', 1)
            else:
                branch = "main"
        else:
            repo_part = remainder
            branch = "main"
            template_name = "" # todo default template name? or raise error?
        git_repo = repo_part
        _item = create_compose_app_from_git_repo_template(app_name, app_dir, git_repo, branch, template_name)
        item.update(_item)

    elif src.startswith("git://") or (src.startswith("https://") and src.endswith(".git")):
        scheme, url_part = src.split("://", 1)
        if '#' in url_part:
            repo_part, branch = src.split('#', 1)
        else:
            repo_part = url_part
            branch = "main"

        _item = create_compose_app_from_git_repo(app_name, app_dir, repo_part, branch)
        item.update(_item)

    elif src.startswith("https://") and (src.endswith(".zip") or src.endswith(".tar.gz") or src.endswith(".tgz")):
        template_url = src
        _item = create_compose_app_from_url_template(app_name, app_dir, template_url)
        item.update(_item)

    else:
        raise ValueError(f"Unsupported source URL scheme: {src}")

    return item



def create_compose_app_from_template_dir(app_name: str, app_dir: str, template_dir: str) -> dict:
    """
    Create a Docker Compose application from a local template directory.

    Args:
        app_name (str): Name of the application.
        app_dir (str): Directory where the application will be created.
        template_dir (str): Path to the local template directory.
    """
    app_path = Path(app_dir)
    if app_path.exists():
        raise FileExistsError(f"Application directory already exists: {app_dir}")

    shutil.copytree(template_dir, app_path)
    print(f"Created application '{app_name}' from template directory '{template_dir}' at '{app_dir}'")

    return {
        "app_name": app_name,
        "app_dir": app_dir,
        "source_url": f"file://{app_dir}",
        "template_url": f"file://{template_dir}",
        "method": "template_dir",
        "template_dir": template_dir,
    }


def create_compose_app_from_git_repo(app_name: str, app_dir: str, git_repo: str, git_branch: str = "main") -> dict:
    """
    Create a Docker Compose application by cloning a git repository.

    Args:
        app_name (str): Name of the application.
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
        "app_name": app_name,
        "app_dir": app_dir,
        "source_url": f"file://{app_dir}",
        "template_url": f"{git_repo}#{git_branch}" if git_repo.startswith("git://") else git_repo,
        "method": "git_repo",
        "git_repo": git_repo,
        "git_branch": git_branch,
    }


def create_compose_app_from_git_repo_template(app_name: str, app_dir: str,
                                              template_git_repo: str, template_git_branch: str = "main",
                                              template_folder: str = "") -> dict:
    """
    Create a Docker Compose application from a template stored in a git repository.

    Args:
        app_name (str): Name of the application.
        app_dir (str): Directory where the application will be created.
        template_git_repo (str): GitHub repository containing templates in the format "user/repo".
        template_git_branch (str): Branch to clone. Default is "main".
        template_folder (str): Name of the template folder inside the repo. Default is "basic".
    """
    app_path = Path(app_dir)
    if app_path.exists():
        raise FileExistsError(f"Application directory already exists: {app_dir}")


    with tempfile.TemporaryDirectory() as tmpdir:
        repo_url = template_git_repo
        git.Repo.clone_from(repo_url, tmpdir, branch=template_git_branch)
        template_path = Path(tmpdir) / template_folder
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_folder}' not found in repository '{template_git_repo}'")
        shutil.copytree(template_path, app_path)
        print(
            f"Created application '{app_name}' from template '{template_folder}' in repo '{template_git_repo}' at '{app_dir}'")

    return {
        "app_name": app_name,
        "app_dir": app_dir,
        "source_url": f"file://{app_dir}",
        "template_url": f"git-template://{template_git_repo}#{template_git_branch}/{template_folder}".rstrip("/"),
        "method": "git_repo_template",
        "template_git_repo": template_git_repo,
        "template_git_branch": template_git_branch,
        "template_dir": template_folder,
    }


def create_compose_app_from_url_template(app_name: str, app_dir: str, template_url: str) -> dict:
    """
    Create a Docker Compose application by downloading a template from a URL (zip or tar.gz).

    Args:
        app_name (str): Name of the application.
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

        print(f"Created application '{app_name}' from URL template '{template_url}' at '{app_dir}'")

    return {
        "app_name": app_name,
        "app_dir": app_dir,
        "source_url": f"file://{app_dir}",
        "template_url": template_url,
        "method": "url_template",
    }

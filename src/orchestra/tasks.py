# This files contains all celery tasks for host orchestration
import re
from pathlib import Path

from mc.config import DATA_DIR
from mc.inventory.item.host import host_item_to_ansible_host
from mc.inventory.storage import get_inventory_storage_instance
from mc.tasks import clone_or_update_git_repo
from orchestra.celery import celery
from orchestra.datamodels import KoAnsibleRunModel
from orchestra.orchestra import ko_playbook_run


@celery.task(bind=True)
def task_run_ansible_playbook_from_repository(self, target: str, repository_url: str, project_dir: str, playbook: str,
                              check: bool = False, **kwargs):
    project_path = None
    # check the repository_url
    if repository_url.startswith("file://"):
        local_path = Path(repository_url[len("file://"):])
        if not local_path.exists():
            raise ValueError(f"Local project path does not exist: {local_path}")
        project_path = local_path / project_dir
    elif repository_url.startswith("git://") or repository_url.startswith("https://") or repository_url.startswith(
            "ssh://"):
        # for git URLs, we clone / upadate the repo to a local directory
        # remove all special characters from repository_url to create a folder
        repo_slug = re.sub(r'[^a-zA-Z0-9\-]', '-', repository_url)
        # repo_path = os.path.join(DATA_DIR, "ansible/projects", repo_slug)
        # project_path = os.path.join(repo_path, project_dir)
        repo_path = Path(DATA_DIR) / "ansible" / "projects" / repo_slug
        project_path = repo_path / project_dir
        try:
            clone_or_update_git_repo(repository_url, str(repo_path.resolve()))
        except Exception as e:
            raise ValueError(f"Project sync failed: {e}")

    # check project path
    if not project_path:
        raise ValueError("Project path could not be determined.")
    if not project_path.exists():
        raise ValueError(f"Project path does not exist: {project_path}")

    # lookup target host from inventory
    storage = get_inventory_storage_instance()
    host_item = storage.get_item_by_name("host", target)
    if not host_item:
        raise ValueError(f"Host '{target}' not found in inventory.")
    print(f"Found host item: {host_item['name']}")

    ansible_host = host_item_to_ansible_host(host_item, "dict")
    print(f"Ansible host data: {ansible_host}")

    try:
        result = ko_playbook_run(
            project_path=str(project_path.resolve()),
            playbook=playbook,
            inventory={'project': {'hosts': {target: ansible_host}}},
            extravars={"target": target},
            cmdline="--check" if check else "",
        )
        print(result)
        return result.model_dump()
    except Exception as e:
        # get stack trace as variable
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        print(f"Error running playbook: {e}")
        return {"error": str(e), "traceback": traceback_str}


@celery.task(bind=True)
def task_run_ansible_playbook(self, target: str, project_path: str, playbook: str,
                              cmdline: str = None, check: bool = False, **kwargs):
    #todo status_handler = celery_ansible_status_handler
    if not target:
        raise ValueError("Target is required")
    if not playbook:
        raise ValueError("Playbook name is required")
    if not project_path:
        raise ValueError("Project path is required")

    if not cmdline:
        cmdline = ""
    if check:
        cmdline += " --check"

    print(f"Running playbook '{playbook}' for target '{target}' in dir '{project_path}'")
    try:
        result: KoAnsibleRunModel = ko_playbook_run(
            project_path=project_path,
            playbook=playbook,
            extravars={"target": target},
            cmdline=cmdline.strip(),
            **kwargs
        )
        return result.model_dump()
    except Exception as e:
        # get stack trace as variable
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        print(f"Error running playbook: {e}")
        return {"error": str(e), "traceback": traceback_str}
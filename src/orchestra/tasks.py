# This files contains all celery tasks for host orchestration
import os

from orchestra.celery import celery
from orchestra.datamodels import KoAnsibleRunModel
from orchestra.orchestra import ko_playbook_run
from orchestra.settings import PROJECTS_DATA_DIR


@celery.task(bind=True)
def task_run_ansible_playbook(self, project: str, target: str, playbook: str, project_path: str = None,
                              cmdline: str = None, check: bool = False, **kwargs):
    #todo status_handler = celery_ansible_status_handler
    if not project:
        raise ValueError("Project name is required")
    if not target:
        raise ValueError("Target is required")
    if not playbook:
        raise ValueError("Playbook name is required")
    if not cmdline:
        cmdline = ""
    #cmdline = "--vault-password-file secrets/vault_password --extra-vars @secrets/vault.yml"

    if check:
        cmdline += " --check"

    #project = "myproject"
    #target = "hostname"
    #playbook = "builtin/dockerhost-debian"
    extravars = {"target": target}
    if not project_path:
        project_path = os.path.join(PROJECTS_DATA_DIR, project)

    print(f"Running playbook '{playbook}' for target '{target}' in project '{project}'")

    try:
        result: KoAnsibleRunModel = ko_playbook_run(
            project=project,
            project_path=project_path,
            playbook=playbook,
            extravars=extravars,
            cmdline=cmdline.strip(),
        )
        return result.model_dump()
    except Exception as e:
        # get stack trace as variable
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)

        print(f"Error running playbook: {e}")
        return {"error": str(e), "traceback": traceback_str}

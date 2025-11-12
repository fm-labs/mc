import os
import shutil
import tempfile
import time
import uuid

from mc.config import RESOURCES_DIR, DATA_DIR
from mc.util.file_util import write_file

from orchestra.ansible.record import insert_ansible_run_record, update_ansible_run_record
from orchestra.ansible.runner import run_ansible_playbook


def ko_playbook_run(project_path: str, playbook: str, **kwargs):
    run_id = str(uuid.uuid4())
    cleanup = kwargs.pop("cleanup", True)
    if not playbook.endswith(".yml") and not playbook.endswith(".yaml"):
        playbook = playbook + ".yml"
    playbook_path = os.path.join(project_path, playbook)

    # verify input parameters
    if not os.path.exists(project_path):
        raise Exception(f"Project directory does not exist: {project_path}")
    if not playbook:
        raise Exception("Playbook is required")
    if not os.path.exists(playbook_path):
        raise Exception(f"Playbook file does not exist: {playbook_path}")

    # create a temporary directory for ansible runner
    privdata_dir = build_ansible_runner_structure(project_path)
    print(f"[{run_id}] Private data dir: {privdata_dir}")
    if not privdata_dir or not os.path.exists(privdata_dir):
        raise Exception("Failed to create temporary ansible runner structure")

    # copy playbook
    shutil.copyfile(playbook_path, f"{privdata_dir}/project/{os.path.basename(playbook_path)}")

    # create ansible job in db
    ansible_run = insert_ansible_run_record(run_id, project_path=project_path, playbook=playbook)

    # execute playbook
    # during playbook execution, the ansible job status is updated in MongoDB (multiple times)
    print(
        f"[{run_id}] Running playbook {playbook} from {project_path} with run ID {run_id} in private data dir {privdata_dir}")
    runner = run_ansible_playbook(run_id=run_id,
                                  private_data_dir=privdata_dir,
                                  playbook=os.path.basename(playbook_path),
                                  **kwargs)

    hostnames_ok = []
    hostnames_failed = []

    # parse the ansible-runner result
    events = []
    for event in runner.events:
        print("Event: ", event)
        events.append(event)
        # if event.get('event') == 'runner_on_ok':
        #     task_result = {
        #         'job_id': job_id,
        #         'task_name': event['event_data'].get('task'),
        #         'host': event['event_data'].get('host'),
        #         'status': event['event'],
        #         'stdout': event['stdout'],
        #         'event_data': event['event_data'],
        #     }
        #     results.append(task_result)

        # collect playbook stats
        #   {
        #     "event": "playbook_on_stats",
        #     "event_data": {
        #       "playbook": "facts-all.yml",
        #       "playbook_uuid": "a071caed-f7f3-423c-a800-74030e966484",
        #       "changed": {},
        #       "dark": {},
        #       "failures": {},
        #       "ignored": {},
        #       "ok": {
        #         "srv03.fmhub": 2,
        #       },
        #       "processed": {
        #         "srv03.fmhub": 1,
        #       },
        #       "rescued": {},
        #       "skipped": {},
        #       "artifact_data": {},
        #       "uuid": "b4683235-9dec-4ab2-9662-21e584c83cbf"
        #     }
        #   }
        # if event.get('event') == 'playbook_on_stats':
        #     stats = event.get('event_data', {})
        #     for hostname, result_count in stats.get('failures', {}).items():
        #         if result_count > 0:
        #             hostnames_failed.append(hostname)
        #     for hostname, result_count in stats.get('ok', {}).items():
        #         if result_count > 0:
        #             hostnames_ok.append(hostname)

        # runner.stats
        # "stats": {
        #     "skipped": {
        #       "srv03.fmhub": 1
        #     },
        #     "ok": {
        #       "srv03.fmhub": 2
        #     },
        #     "dark": {},
        #     "failures": {},
        #     "ignored": {},
        #     "rescued": {},
        #     "processed": {
        #       "srv03.fmhub": 1
        #     },
        #     "changed": {}
        #   },

    ansible_run.status = runner.status
    ansible_run.rc = runner.rc
    ansible_run.stdout = runner.stdout.read()
    ansible_run.stderr = runner.stderr.read()
    ansible_run.events = events
    ansible_run.stats = runner.stats
    ansible_run.finished_at = time.time()

    # update the run record and store the result in MongoDB
    update_ansible_run_record(ansible_run)

    # Remove the temporary ansible runner structure
    if cleanup:
        print("Cleaning up...")
        try:
            shutil.rmtree(privdata_dir, ignore_errors=False)
        except OSError as e:
            print(f"[{run_id}] Error while cleanup: {privdata_dir} : {e.strerror}")
            shutil.rmtree(privdata_dir, ignore_errors=True)

    return ansible_run


def build_ansible_runner_structure(project_path: str):
    """
    Build a temporary ansible runner structure for the given project.
    See: https://ansible.readthedocs.io/projects/runner/en/stable/intro/#runner-input-directory-hierarchy

    The project has the following directory structure:
    .
    ├── project_name
    │   ├── inventory
    │   ├── playbooks
    │   ├── secrets

    The ansible runner expects the following directory structure:
    .
    ├── env
    │   ├── envvars
    │   ├── extravars
    │   ├── passwords
    │   ├── cmdline
    │   ├── settings
    │   └── ssh_key
    ├── inventory
    │   └── hosts
    └── project
        ├── test.yml
        └── roles
            └── testrole
                ├── defaults
                ├── handlers
                ├── meta
                ├── README.md
                ├── tasks
                ├── tests
                └── vars

    :param project_path: str - path to the ansible project
    :return: str - path to the temporary ansible runner structure
    """
    tmp_base_dir = f"{DATA_DIR}/ansible/tmp"
    os.makedirs(tmp_base_dir, exist_ok=True)
    tmp_private_data_dir = tempfile.mkdtemp(prefix="ansible-priv-", dir=tmp_base_dir)
    print(f"Creating temporary ansible runner structure in {tmp_private_data_dir}")

    def _read_project_env_file(filename: str):
        file_path = os.path.join(project_path, filename)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            return f.read()

    try:
        # env
        envvars = _read_project_env_file("env/envvars")
        if envvars is None:
            envvars = ""

        #envvars += f"ANSIBLE_HOME={os.path.join(tmp_private_data_dir)}\n"
        #envvars += f"ANSIBLE_CONFIG={os.path.join(tmp_private_data_dir,'ansible.cfg')}\n"
        #envvars += f"ANSIBLE_INVENTORY={os.path.join(tmp_private_data_dir, 'inventory', 'hosts')}\n"
        #envvars += f"ANSIBLE_PRIVATE_DATA_DIR={tmp_private_data_dir}\n"
        #envvars += f"ANSIBLE_RUNNER_PROJECT={project_path}\n"
        #envvars += f"ANSIBLE_RUNNER_PLAYBOOK={os.path.join(project_path, 'playbook.yml')}\n"
        #envvars += f"ANSIBLE_RUNNER_STDOUT_CALLBACK=orchestra.ansible.runner.KoStdoutCallback\n"
        #envvars += f"ANSIBLE_RUNNER_STDOUT_CALLBACK_CONFIG={os.path.join(project_path, 'stdout_callback_config.yml')}\n"
        #envvars += f"ANSIBLE_HOME={os.path.join(tmp_private_data_dir)}\n"
        envvars += f"ANSIBLE_NOCOLOR: 1\n"
        envvars += f"ANSIBLE_NOCOWS: 1\n"

        # add RESOURCE_DIR/roles to ANSIBLE_ROLES_PATH
        project_roles_path = os.path.join(project_path, "roles")
        shared_roles_path = os.path.join(RESOURCES_DIR, "ansible", "roles")
        envvars += f"ANSIBLE_ROLES_PATH: ./roles:{project_roles_path}:{shared_roles_path}\n"
        write_file(os.path.join(tmp_private_data_dir, "env", "envvars"), envvars)

        # extravars
        extravars = _read_project_env_file("env/extravars")
        if extravars is None:
            extravars = "{}"
        write_file(os.path.join(tmp_private_data_dir, "env", "extravars"), extravars)

        # passwords
        passwords = _read_project_env_file("env/passwords")
        if passwords is None:
            passwords = ""
        write_file(os.path.join(tmp_private_data_dir, "env", "passwords"), passwords)

        # cmdline
        cmdline = _read_project_env_file("env/cmdline")
        if cmdline is None:
            cmdline = ""
        write_file(os.path.join(tmp_private_data_dir, "env", "cmdline"), cmdline)

        # settings
        settings = _read_project_env_file("env/settings")
        if settings is None:
            settings = ""
        write_file(os.path.join(tmp_private_data_dir, "env", "settings"), settings)

        # ssh_key
        ssh_key = _read_project_env_file("env/ssh_key")
        if ssh_key is None:
            ssh_key = ""
        write_file(os.path.join(tmp_private_data_dir, "env", "ssh_key"), ssh_key)

        # vault_password
        vault_password = _read_project_env_file("env/vault_password")
        if vault_password is not None:
            write_file(os.path.join(tmp_private_data_dir, "env", "vault_password"), vault_password)


        # inventory
        #inventory_dir = os.path.join(project_path, "inventory")
        #if not os.path.exists(inventory_dir):
        #    raise Exception(f"Inventory directory {inventory_dir} does not exist")
        #tmp_inventory_dir = os.path.join(tmp_private_data_dir, "inventory")
        #os.symlink(inventory_dir, tmp_inventory_dir)

        # project directory
        tmp_project_dir = os.path.join(tmp_private_data_dir, "project")
        os.makedirs(tmp_project_dir, exist_ok=True)

        # link project roles and playbooks to the temporary project directory
        #roles_dir = os.path.join(project_path, "roles")
        #if os.path.exists(roles_dir):
        #    os.symlink(roles_dir, os.path.join(tmp_project_dir, "roles"))

        #playbooks_dir = os.path.join(project_path, "playbooks")
        #if os.path.exists(playbooks_dir):
        #    os.symlink(playbooks_dir, os.path.join(tmp_project_dir, "playbooks"))

        # secrets
        secrets_dir = os.path.join(project_path, "secrets")
        if os.path.exists(secrets_dir):
            os.symlink(secrets_dir, os.path.join(tmp_project_dir, "secrets"))

        # link the built-in ansible roles and playbooks
        #builtin_playbooks_dir = os.path.join(RESOURCES_DIR, "ansible", "playbooks")
        #if os.path.exists(builtin_playbooks_dir):
        #    os.symlink(builtin_playbooks_dir, os.path.join(tmp_project_dir, "builtin"))

        # builtin_roles_dir = os.path.join(RESOURCES_DIR, "ansible", "roles")
        # if os.path.exists(builtin_roles_dir):
        #     os.symlink(builtin_roles_dir, os.path.join(tmp_project_dir, "builtin-roles"))
    except Exception as e:
        # cleanup on error
        try:
            print("Error during building ansible runner structure, cleaning up...", e)
            shutil.rmtree(tmp_private_data_dir, ignore_errors=False)
        except OSError as oe:
            print(f"Error while cleanup after failure: {tmp_private_data_dir} : {oe.strerror}")
            shutil.rmtree(tmp_private_data_dir, ignore_errors=True)
        raise e

    return tmp_private_data_dir

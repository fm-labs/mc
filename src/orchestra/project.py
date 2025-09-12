import os
from tempfile import mkdtemp

from orchestra.settings import DATA_DIR, TMP_DIR, RESOURCES_DIR
from orchestra.utils.file_util import write_file

PROJECTS_DATA_DIR=os.path.join(DATA_DIR, "projects")

def list_projects():
    """
    List all projects in the projects data directory.
    Each project is a directory in the projects data directory.

    :return:
    """
    projects = []
    if os.path.exists(PROJECTS_DATA_DIR):
        for project in os.listdir(PROJECTS_DATA_DIR):
            project_path = os.path.join(PROJECTS_DATA_DIR, project)
            if os.path.isdir(project_path) and not project.startswith(".") and not project.startswith("_"):
                projects.append(project)
    return projects


def get_project_path(project: str):
    """
    Get the path to the project directory.
    :param project: str - name of the project
    :return: str - path to the project directory
    """
    project_path = os.path.join(PROJECTS_DATA_DIR, project)
    if not os.path.exists(project_path):
        raise Exception(f"Project {project} does not exist in {PROJECTS_DATA_DIR}")
    return project_path


def build_ansible_runner_structure(project: str):
    """
    Build a temporary ansible runner structure for the given project.

    See: https://ansible.readthedocs.io/projects/runner/en/stable/intro/#runner-input-directory-hierarchy

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


    :param project: str - name of the project
    :return: str - path to the temporary ansible runner structure
    """
    project_path = os.path.join(PROJECTS_DATA_DIR, project)
    if not os.path.exists(project_path):
        raise Exception(f"Project {project} does not exist in {PROJECTS_DATA_DIR}")

    # create base folder for temporary ansible runner files
    tmp_prefix = f"{project}."
    tmp_dir = TMP_DIR if TMP_DIR else os.path.join(DATA_DIR, "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    tmp_private_data_dir = mkdtemp(dir=tmp_dir, prefix=tmp_prefix)
    if not os.path.exists(tmp_private_data_dir):
        os.makedirs(tmp_private_data_dir)

    def _read_project_env_file(filename: str):
        """
        Read the contents of a file and return it as a string.
        :param filename: str - path to the file
        :return: str - contents of the file
        """
        file_path = os.path.join(project_path, filename)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r") as f:
            return f.read()

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
    shared_roles_path = os.path.join(RESOURCES_DIR, "roles")
    envvars += f"ANSIBLE_ROLES_PATH: ./roles:{project_roles_path}:{shared_roles_path}\n"
    write_file(os.path.join(tmp_private_data_dir, "env", "envvars"), envvars)


    extravars = _read_project_env_file("env/extravars")
    if extravars is None:
        extravars = "{}"
    write_file(os.path.join(tmp_private_data_dir, "env", "extravars"), extravars)


    passwords = _read_project_env_file("env/passwords")
    if passwords is None:
        passwords = ""
    write_file(os.path.join(tmp_private_data_dir, "env", "passwords"), passwords)


    cmdline = _read_project_env_file("env/cmdline")
    if cmdline is None:
        cmdline = ""
    write_file(os.path.join(tmp_private_data_dir, "env", "cmdline"), cmdline)


    settings = _read_project_env_file("env/settings")
    if settings is None:
        settings = ""
    write_file(os.path.join(tmp_private_data_dir, "env", "settings"), settings)


    ssh_key = _read_project_env_file("env/ssh_key")
    if ssh_key is None:
        ssh_key = ""
    write_file(os.path.join(tmp_private_data_dir, "env", "ssh_key"), ssh_key)

    vault_password = _read_project_env_file("env/vault_password")
    if vault_password is not None:
        write_file(os.path.join(tmp_private_data_dir, "env", "vault_password"), vault_password)
    
    
    # inventory
    inventory_dir = os.path.join(project_path, "inventory")
    if not os.path.exists(inventory_dir):
        raise Exception(f"Inventory directory {inventory_dir} does not exist in {project_path}")
    tmp_inventory_dir = os.path.join(tmp_private_data_dir, "inventory")
    os.symlink(inventory_dir, tmp_inventory_dir)

    # project directory
    tmp_project_dir = os.path.join(tmp_private_data_dir, "project")
    os.makedirs(tmp_project_dir, exist_ok=True)

    # link project roles and playbooks
    roles_dir = os.path.join(project_path, "roles")
    if os.path.exists(roles_dir):
        os.symlink(roles_dir, os.path.join(tmp_project_dir, "roles"))

    playbooks_dir = os.path.join(project_path, "playbooks")
    if os.path.exists(playbooks_dir):
        os.symlink(playbooks_dir, os.path.join(tmp_project_dir, "playbooks"))

    # secrets
    secrets_dir = os.path.join(project_path, "secrets")
    if os.path.exists(secrets_dir):
        os.symlink(secrets_dir, os.path.join(tmp_project_dir, "secrets"))


    # link the built-in ansible roles and playbooks
    builtin_playbooks_dir = os.path.join(RESOURCES_DIR, "playbooks")
    if os.path.exists(builtin_playbooks_dir):
        os.symlink(builtin_playbooks_dir, os.path.join(tmp_project_dir, "builtin"))

    # builtin_roles_dir = os.path.join(RESOURCES_DIR, "roles")
    # if os.path.exists(builtin_roles_dir):
    #     os.symlink(builtin_roles_dir, os.path.join(tmp_project_dir, "builtin-roles"))

    return tmp_private_data_dir


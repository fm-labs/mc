from pathlib import Path

import paramiko

from mc.config import RESOURCES_DIR
from mc.inventory.item.app_stack_helper import create_app_stack_from_template_dir
from mc.tasks import task_deploy_compose_project
from mc.util.ssh_util import sftp_copy_file, ssh_mkdir_recursive
from mc.util.sshpy_helper import ssh_connect


def get_ssh_client_from_host_url(host_url: str) -> paramiko.SSHClient:

    if not host_url.startswith("ssh://"):
        raise ValueError("Host URL must start with ssh:// for SSH connections.")

    # Remove the ssh:// prefix
    ssh_url = host_url[len("ssh://"):]

    # Parse the SSH URL to extract username, hostname, and port
    if "@" in ssh_url:
        user_host, _, port_part = ssh_url.partition(":")
        username, _, hostname = user_host.partition("@")
    else:
        hostname, _, port_part = ssh_url.partition(":")
        username = None

    port = int(port_part) if port_part else 22
    ssh_client = ssh_connect(hostname=hostname, port=port, username=username)
    return ssh_client


def handle_container_host_docker_login(item: dict, action_params: dict) -> dict:
    """
    Copies Docker credentials to the container host for Docker registry authentication.
    Credentials are read from the local Docker config file located at ~/.docker/config.json.
    """
    host_url = item.get("url")
    if not host_url:
        raise ValueError("Container host URL not found in item.")

    if not host_url.startswith("ssh://"):
        raise ValueError("Docker login action is only supported for SSH container hosts.")

    docker_config_file = Path.home() / ".docker" / "config.json"
    if not docker_config_file.exists():
        raise FileNotFoundError(f"Docker config file not found at {docker_config_file}")

    # copy the docker config file to the container host
    try:
        local_docker_config_file = str(docker_config_file)
        remote_docker_config_file = ".docker/config.json"

        ssh_client = get_ssh_client_from_host_url(host_url)
        #sftp_mkdir(ssh_client, ".docker", mode=0o700)
        ssh_mkdir_recursive(ssh_client, ".docker", mode=0o700)
        sftp_copy_file(ssh_client, local_docker_config_file, remote_docker_config_file)
        ssh_client.close()
    except Exception as exc:
        print(str(exc))
        raise RuntimeError(f"Failed to sync docker auth via SSH: {exc}") from exc

    return {"status": "success", "message": "Docker credentials copied to container host."}



def handle_container_host_deploy_template(item: dict, action_params: dict) -> dict:
    host_url = item.get("url")
    if not host_url:
        raise ValueError("Container host URL not found in item.")

    template_name = action_params.get("template_name")
    if not template_name:
        raise ValueError("Template name not provided in action parameters.")

    project_name = action_params.get("project_name")
    if not project_name:
        raise ValueError("Project name not provided in action parameters.")

    app_name = action_params.get("app_name")
    if not app_name:
        raise ValueError("App name not provided in action parameters.")

    create_app = action_params.get("create_app", "false").lower() == "true"
    template_dir_path = Path(RESOURCES_DIR) / "compose-templates" / template_name

    if not create_app:
        if not template_dir_path.exists() or not template_dir_path.is_dir():
            raise FileNotFoundError(f"{template_dir_path} does not exist")

        return task_deploy_compose_project(host_url=host_url,
                                           app_name=app_name,
                                           app_dir=template_dir_path.name)
    else:
        # the app dir is where the compose app will be created
        app_dir = Path(f"data/projects/{project_name}/apps/{app_name}")
        item = create_app_stack_from_template_dir(stack_name=app_name,
                                                  app_dir=app_dir.name,
                                                  template_dir=template_dir_path.name)

        # todo store the app stack item in inventory
        return task_deploy_compose_project(host_url=host_url,
                                           app_name=app_name,
                                           app_dir=app_dir.name)


actions = {
    "docker_login": handle_container_host_docker_login,
    "deploy_template": handle_container_host_deploy_template,
}

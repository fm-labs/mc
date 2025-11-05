import subprocess
from pathlib import Path
import shutil

from mc.config import DATA_DIR
from mc.inventory.item.compose_project import handle_compose_project_configure, handle_compose_project_deploy
from mc.inventory.items import create_inventory_item
from mc.inventory.storage import get_inventory_storage_instance
from orchestra.tasks import task_run_ansible_playbook


def handle_host_ping(item: dict, action_params: dict) -> dict:
    props = item.get("properties", {})
    #host_name = props.get("ssh_hostname", props.get("hostname", item.get("name")))
    #if not host_name:
    #   raise ValueError("Hostname not found in item properties.")
    #host_ip = item.get("properties", {}).get("ip_address")
    #if not host_ip:
    #    raise ValueError("IP address not found in item properties.")
    ping_target = props.get("ssh_hostname", props.get("ip_address", props.get("hostname", item.get("name"))))
    try:
        packet_count = action_params.get("count", "1")
        output = subprocess.check_output(["ping", "-c", packet_count, "-W", "1", ping_target], universal_newlines=True)

        # parse output to check for success
        print("OUTPUT:", output)
        #if f"{packet_count} packets transmitted, {packet_count} packets received" not in output:
        #    raise subprocess.CalledProcessError(returncode=1, cmd="ping", output=output)
        if "0% packet loss" not in output:
            raise subprocess.CalledProcessError(returncode=1, cmd="ping", output=output)

        return {"status": "reachable", "output": output}
    except subprocess.CalledProcessError as e:
        return {"status": "unreachable", "output": e.stdout, "error": str(e)}


def handle_host_run_ansible_playbook(item: dict, action_params: dict) -> dict:
    #host_name = item.get("properties", {}).get("hostname")
    #if not host_name:
    #    raise ValueError("Hostname not found in item properties.")
    if not action_params.get("project"):
        raise ValueError("Parameter 'project' is required.")
    if not action_params.get("target"):
        raise ValueError("Parameter 'target' is required.")
    if not action_params.get("playbook"):
        raise ValueError("Parameter 'playbook' is required.")

    task = task_run_ansible_playbook.apply_async(kwargs={
        "project": action_params.get("project"),
        "target": action_params.get("target"),
        "playbook": action_params.get("playbook"),
        "cmdline": action_params.get("cmdline", ""),
        "check": action_params.get("check", False),
    })
    return {"task_id": task.id}


def handle_host_ssh_probe(item: dict, action_params: dict) -> dict:
    host_name = item.get("properties", {}).get("hostname")
    if not host_name:
        raise ValueError("Hostname not found in item properties.")
    import socket
    port = action_params.get("port", 22)
    timeout = action_params.get("timeout", 5)
    try:
        with socket.create_connection((host_name, port), timeout=timeout):
            return {"status": "open", "port": port}
    except (socket.timeout, ConnectionRefusedError):
        return {"status": "closed", "port": port}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def handle_host_setup_container_host(item: dict, action_params: dict) -> dict:
    # todo run the appropriate ansible playbook to setup container host
    return {"status": "error", "message": "Setup container host action is not implemented yet."}


def handle_host_setup_webstack(item: dict, action_params: dict) -> dict:
    # todo run the appropriate compose project template to setup web host

    host_name = item.get("properties", {}).get("hostname")
    if not host_name:
        raise ValueError("Hostname not found in item properties.")

    project_name = action_params.get("project_name")
    if not project_name:
        raise ValueError("Parameter 'project_name' is required.")

    webstack_enabled = item.get("properties", {}).get("webstack_enabled", True)
    if not webstack_enabled:
        raise ValueError("Parameter 'webstack_enabled' is required.")

    app_name = f"traefik-ssl-{host_name}"

    # 1. create a compose project from template
    # check if compose project already exists
    storage = get_inventory_storage_instance()
    existing_cp = storage.get_item_by_name("compose_project", app_name)
    if existing_cp:
        cp_item = existing_cp
    else:
        template_dir = "resources/compose-templates/traefik-ssl"
        app_dir = f"projects/{project_name}/apps/{app_name}"
        target_dir = f"{DATA_DIR}/{app_dir}"
        create_compose_project_app_dir_from_template(template_dir, target_dir)

        cp = {
            "source_url": f"file://{template_dir}",
            "target_url": f"ssh://{host_name}",
            "domain_name": "",
            "project_name": project_name,
            "app_name": app_name,
            "app_dir": app_dir,
            "template_url": f"file://{template_dir}",
            "description": "Traefik SSL Web Host",
            "version": "1.0.0"
        }
        cp_item = {
            "name": app_name,
            "properties": cp
        }
        #storage.save_item("compose_project", cp_item)
        cp_item = create_inventory_item("compose_project", cp_item)

    # 2. configure the compose project to run on the host
    handle_compose_project_configure(cp_item, {})
    # 3. deploy the compose project to the host
    return handle_compose_project_deploy(cp_item, {})




def create_compose_project_app_dir_from_template(template_dir: str, target_dir: str) -> None:
    # check if target_dir exists
    target_path = Path(target_dir)
    if target_path.exists():
        raise FileExistsError(f"Target directory '{target_dir}' already exists.")

    template_path = Path(template_dir)
    if not template_path.exists():
        raise FileNotFoundError(f"Template directory '{template_dir}' does not exist.")

    # copy template directory to target directory
    shutil.copytree(template_dir, target_dir)


actions = {
    "ping": handle_host_ping,
    "run_playbook": handle_host_run_ansible_playbook,
    "ssh_connect": handle_host_ssh_probe,
    "setup_container_host": handle_host_setup_container_host,
    "setup_webstack": handle_host_setup_webstack,
}
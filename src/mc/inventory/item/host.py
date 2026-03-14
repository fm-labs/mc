import subprocess

from mc.config import RESOURCES_DIR
from mc.inventory.item.app_stack import handle_app_stack_action_prepare, handle_app_stack_action_deploy, \
    handle_app_stack_action_sync
from mc.inventory.items import create_inventory_item
from mc.inventory.storage import get_inventory_storage_instance
from orchestra.tasks import task_run_ansible_playbook


def handle_host_ping(item: dict, action_params: dict) -> dict:
    props = item
    #host_name = props.get("ssh_hostname", props.get("hostname", item.get("name")))
    #if not host_name:
    #   raise ValueError("Hostname not found in item.")
    #host_ip = item.get("ip_address")
    #if not host_ip:
    #    raise ValueError("IP address not found in item.")
    ping_target = props.get("ssh_hostname", props.get("ip_address", props.get("hostname", item.get("name"))))
    try:
        print("Ping: ", ping_target)
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
    hostname = item.get("ssh_hostname")
    if not hostname:
        raise ValueError("Hostname not found in item.")
    if not action_params.get("playbook"):
        raise ValueError("Parameter 'playbook' is required.")

    task = task_run_ansible_playbook.apply_async(kwargs={
        "project_path": f"{RESOURCES_DIR}/ansible",
        "target": hostname,
        "playbook": "playbooks/" + action_params.get("playbook"),
        "check": action_params.get("check", False),
    })
    # task = task_run_ansible_playbook_from_repository.apply_async(kwargs={
    #     "repository_url": f"file://{RESOURCES_DIR}",
    #     "project_dir": "ansible/",
    #     "target": hostname,
    #     "playbook": "playbooks/" + action_params.get("playbook"),
    #     "check": action_params.get("check", False),
    # })
    return {"task_id": task.id}


def handle_host_ssh_probe(item: dict, action_params: dict) -> dict:
    hostname = item.get("hostname")
    if not hostname:
        raise ValueError("Hostname not found in item.")
    import socket
    port = action_params.get("port", 22)
    timeout = action_params.get("timeout", 5)
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
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

    hostname = item.get("hostname")
    if not hostname:
        raise ValueError("Hostname not found in item.")

    project_name = action_params.get("project_name")
    if not project_name:
        raise ValueError("Parameter 'project_name' is required.")

    webstack_enabled = item.get("webstack_enabled", True)
    if not webstack_enabled:
        raise ValueError("Parameter 'webstack_enabled' is required.")

    app_name = f"traefik-ssl-{hostname}"

    # 1. create an app stack item if not exists
    storage = get_inventory_storage_instance()
    existing_stack = storage.get_item_by_name("app_stack", app_name)
    if existing_stack:
        stack_item = existing_stack
    else:
        stack_item = {
            "name": app_name,
            "properties": {
                "source_url": f"file://{RESOURCES_DIR}/compose-templates",
                "stackfile": "traefik-ssl/compose.yaml",
                "container_host": hostname,
                "domain_name": "",
                "description": "Traefik SSL Web Host",
                "version": "1.0.0"
            }
        }
        stack_item = create_inventory_item("app_stack", stack_item) # assigns ID

    # 2. sync the compose project from template repository
    handle_app_stack_action_sync(stack_item, {"background": False})
    # 3. configure the compose project to run on the host
    handle_app_stack_action_prepare(stack_item, {"background": False})
    # 4. deploy the compose project to the host
    return handle_app_stack_action_deploy(stack_item, {"background": True})



# def create_compose_project_app_dir_from_template(template_dir: str, target_dir: str) -> None:
#     # check if target_dir exists
#     target_path = Path(target_dir)
#     if target_path.exists():
#         raise FileExistsError(f"Target directory '{target_dir}' already exists.")
#
#     template_path = Path(template_dir)
#     if not template_path.exists():
#         raise FileNotFoundError(f"Template directory '{template_dir}' does not exist.")
#
#     # copy template directory to target directory
#     shutil.copytree(template_dir, target_dir)


actions = {
    "ping": handle_host_ping,
    "run_playbook": handle_host_run_ansible_playbook,
    "ssh_connect": handle_host_ssh_probe,
    "setup_container_host": handle_host_setup_container_host,
    "setup_webstack": handle_host_setup_webstack,
}
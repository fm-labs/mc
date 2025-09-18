import uuid
from pathlib import Path
from time import time

from kloudia import config
from kloudia.config import DATA_DIR, HOST_DATA_DIR
from kloudia.inventory.storage import get_inventory_storage_instance
from kloudia.plugin.tools.tasks import task_subprocess_run
from kloudia.plugin.xscan.tasks import task_parse_scan_result


def handle_inventory_item_action(item_type: str, uuid: str, action_name: str, action_params: dict) -> dict:
    storage = get_inventory_storage_instance()
    item = storage.get_item(item_type, uuid)
    if not item:
        #return {"error": f"Item '{uuid}' of type '{item_type}' not found."}
        raise ValueError(f"Item '{uuid}' of type '{item_type}' not found.")

    module_name = f"kloudia.inventory.actions"
    method_name = f"handle_{item_type}_item_{action_name}"

    try:
        module = __import__(module_name, fromlist=[method_name])
        method = getattr(module, method_name)
    except (ImportError, AttributeError) as e:
        #return {"error": f"Action '{action_name}' for item type '{item_type}' is not implemented."}
        raise NotImplementedError(f"Action '{action_name}' for item type '{item_type}' is not implemented.") from e

    return method(item, action_params)


def handle_repository_item_scan(item: dict, action_params: dict) -> dict:
    # creating a unique output directory for the scan results
    # the directory will be mapped to the docker container
    scan_id = f"{str(int(time()))}-{uuid.uuid4().hex}"
    scan_output_dir = f"inventory/repositories/{item['name']}/xscan/{scan_id}"
    scan_output_path = Path(DATA_DIR) / scan_output_dir
    scan_output_path.mkdir(parents=True, exist_ok=True)

    # for docker-in-docker volume mapping we need the real host path
    # mounts /path/on/hostmachine/data/scans/xyz -> /data/ in the scan container
    host_output_path = f"{HOST_DATA_DIR}/{scan_output_dir}"

    repo_url = item.get("properties", {}).get("url")
    if not repo_url:
        return {"error": "Repository URL not found in item properties."}

    cmd = ["xscan", "repo", repo_url, "--output-dir", "/data", "--ref", scan_id]
    docker_cmd = ["docker", "run", "--rm",
                  "-e", "GIT_TERMINAL_PROMPT=0",  # disable git prompts for authentication
                  "-e", f"GITHUB_TOKEN={config.GITHUB_TOKEN}",
                  "-v", f"{host_output_path}:/data", "kloudia-xscan:latest"] + cmd

    #task = task_subprocess_run.delay(docker_cmd)
    task = task_subprocess_run.apply_async(args=(docker_cmd,),
                                           link=task_parse_scan_result.si(ref=scan_id, result_dir=str(scan_output_dir)),)

    # save_inventory_scan_metadata(item, scan_id, task_id)

    return {"task_id": task.id}


def handle_internet_domain_item_ping(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["ping", "-c", "4", domain]
    task = task_subprocess_run.delay(cmd)
    return {"task_id": task.id}


def handle_internet_domain_item_whois(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["whois", domain]
    task = task_subprocess_run.delay(cmd)
    return {"task_id": task.id}


def handle_internet_domain_item_dig(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["dig", domain, "+short"]
    task = task_subprocess_run.delay(cmd)
    return {"task_id": task.id}


# INVENTORY_ACTIONS = {
#     "repository": {
#         "scan": handle_repository_item_scan,
#         #"clone": handle_repository_item_clone,
#         #"fork": handle_repository_item_fork,
#         #"activate": handle_inventory_item_activate,
#         #"deactivate": handle_inventory_item_deactivate,
#     },
#     "container_image": {
#         #"scan": handle_container_image_item_scan,
#     },
#     "internet_domain": {
#         "ping": handle_internet_domain_item_ping,
#         "whois": handle_internet_domain_item_whois,
#         "dig": handle_internet_domain_item_dig,
#         #"scan": handle_internet_domain_item_scan,
#     },
# }

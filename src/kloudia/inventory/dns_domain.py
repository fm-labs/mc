from typing import Optional
import uuid
from pathlib import Path
from time import time

from pydantic import BaseModel

from kloudia import config
from kloudia.config import DATA_DIR, HOST_DATA_DIR
from kloudia.plugin.tools.tasks import task_subprocess_run, task_subprocess_stream


class DnsDomainInventory(BaseModel):
    registrar: Optional[str]


def handle_dns_domain_item_ping(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["ping", "-c", "4", domain]
    task = task_subprocess_stream.delay(cmd)
    return {"task_id": task.id}


def handle_dns_domain_item_whois(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["whois", domain]
    task = task_subprocess_stream.delay(cmd)
    return {"task_id": task.id}


def handle_dns_domain_item_dig(item: dict, action_params: dict) -> dict:
    domain = item.get("name")
    if not domain:
        return {"error": "Domain name not found in item."}

    cmd = ["dig", domain, "+short"]
    task = task_subprocess_run.delay(cmd)
    return {"task_id": task.id}


def handle_dns_domain_item_scan(item: dict, action_params: dict) -> dict:
    # creating a unique output directory for the scan results
    # the directory will be mapped to the docker container
    scan_id = f"{str(int(time()))}-{uuid.uuid4().hex}"
    scan_output_dir = f"xscan/{scan_id}"
    scan_output_path = Path(DATA_DIR) / scan_output_dir
    scan_output_path.mkdir(parents=True, exist_ok=True)

    # for docker-in-docker volume mapping we need the real host path
    # mounts /path/on/hostmachine/data/scans/xyz -> /data/ in the scan container
    host_output_path = f"{HOST_DATA_DIR}/{scan_output_dir}"

    domain_name = item.get("name")
    if not domain_name:
        return {"error": "Repository URL not found in item properties."}

    cmd = ["xscan", "domain", domain_name, "--output-dir", "/data", "--ref", scan_id]
    docker_cmd = ["docker", "run", "--rm",
                  "-e", "GIT_TERMINAL_PROMPT=0",  # disable git prompts for authentication
                  "-e", f"GITHUB_TOKEN={config.GITHUB_TOKEN}",
                  "-v", f"{host_output_path}:/data", "kloudia-xscan:latest"] + cmd

    #task = task_subprocess_run.delay(docker_cmd)
    task = task_subprocess_run.apply_async(args=(docker_cmd,))

    # save_inventory_scan_metadata(item, scan_id, task_id)

    return {"task_id": task.id}

#//////////////////////////////////////////////////////////////////////////////////////////

actions = {
    "ping": handle_dns_domain_item_ping,
    "whois": handle_dns_domain_item_whois,
    "dig": handle_dns_domain_item_dig,
    "scan": handle_dns_domain_item_scan,
}

views = {}

routes = {}

inventory = {
    "name": "dns_domain",
    "description": "DNS Domain",
    "category": "networking",
    "version": "1.0.0",
    "model": DnsDomainInventory,
    "actions": actions,
}
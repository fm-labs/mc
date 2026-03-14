import uuid
from pathlib import Path
from time import time
from typing import Optional

from pydantic import BaseModel

from mc import config
from mc.config import DATA_DIR, HOST_DATA_DIR
from mc.plugin.tools.tasks import task_subprocess_stream
from mc.plugin.xscan.tasks import task_parse_scan_result


class RepositoryInventoryModel(BaseModel):
    #name: str
    url: str
    description: Optional[str] = None
    private: Optional[bool] = False
    default_branch: Optional[str] = "main"
    ssh_url: Optional[str] = None




def handle_repository_item_scan(item: dict, action_params: dict) -> dict:
    # creating a unique output directory for the scan results
    # the directory will be mapped to the docker container
    scan_id = f"{str(int(time()))}-{uuid.uuid4().hex}"
    scan_output_dir = f"xscan/{scan_id}"
    scan_output_path = Path(DATA_DIR) / scan_output_dir
    scan_output_path.mkdir(parents=True, exist_ok=True)

    # for docker-in-docker volume mapping we need the real host path
    # mounts /path/on/hostmachine/data/scans/xyz -> /data/ in the scan container
    host_output_path = f"{HOST_DATA_DIR}/{scan_output_dir}"

    repo_url = item.get("url")
    if not repo_url:
        return {"error": "Repository URL not found in item."}

    cmd = ["xscan", "repo", repo_url, "--output-dir", "/data", "--ref", scan_id]
    docker_cmd = ["docker", "run", "--rm",
                  "-e", "GIT_TERMINAL_PROMPT=0",  # disable git prompts for authentication
                  "-e", f"GITHUB_TOKEN={config.GITHUB_TOKEN}",
                  "-v", f"{host_output_path}:/data", "kloudia-xscan:latest"] + cmd

    #task = task_subprocess_run.delay(docker_cmd)
    task = task_subprocess_stream.apply_async(args=(docker_cmd,),
                                           link=task_parse_scan_result.si(ref=scan_id, result_dir=str(scan_output_dir)),)

    # save_inventory_scan_metadata(item, scan_id, task_id)

    return {"task_id": task.id}

#//////////////////////////////////////////////////////////////////////////////////////////

actions = {
    "scan": handle_repository_item_scan,
}

views = {}

routes = {}

inventory = {
    "name": "repository",
    "description": "Software repositories",
    "category": "development",
    "version": "1.0.0",
    "model": RepositoryInventoryModel,
    "actions": actions,
}
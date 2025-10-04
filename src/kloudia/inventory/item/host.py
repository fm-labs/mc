from orchestra.tasks import task_run_ansible_playbook

def handle_host_ping(item: dict, action_params: dict) -> dict:
    host_name = item.get("properties", {}).get("hostname")
    if not host_name:
        raise ValueError("Hostname not found in item properties.")
    import subprocess
    try:
        output = subprocess.check_output(["ping", "-c", "4", "-W", "1", host_name], universal_newlines=True)
        return {"status": "reachable", "output": output}
    except subprocess.CalledProcessError as e:
        return {"status": "unreachable", "error": str(e)}


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



actions = {
    "ping": handle_host_ping,
    "run_playbook": handle_host_run_ansible_playbook,
}
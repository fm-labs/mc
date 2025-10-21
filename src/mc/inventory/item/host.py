import subprocess

from orchestra.tasks import task_run_ansible_playbook


def handle_host_ping(item: dict, action_params: dict) -> dict:
    props = item.get("properties", {})
    host_name = props.get("ssh_hostname", props.get("hostname", item.get("name")))
    if not host_name:
       raise ValueError("Hostname not found in item properties.")
    #host_ip = item.get("properties", {}).get("ip_address")
    #if not host_ip:
    #    raise ValueError("IP address not found in item properties.")
    try:
        packet_count = action_params.get("count", "1")
        output = subprocess.check_output(["ping", "-c", packet_count, "-W", "1", host_name], universal_newlines=True)

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


actions = {
    "ping": handle_host_ping,
    "run_playbook": handle_host_run_ansible_playbook,
    "ssh_connect": handle_host_ssh_probe,
}
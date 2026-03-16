import subprocess

import requests


def handle_node_ping(item: dict, action_params: dict) -> dict:

    url = item.get("url")
    if not url or "://" not in url:
        raise ValueError("Invalid URL")

    # extract the hostname or IP from the URL
    host_with_port_path = url.split("://", 1)[1]
    if "/" in host_with_port_path:
        host_with_port = host_with_port_path.split("/", 1)[0]
    else:
        host_with_port = host_with_port_path
    if ":" in host_with_port:
        host = host_with_port.split(":", 1)[0]
    else:
        host = host_with_port

    ping_target = host
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


def handle_api_probe(item: dict, action_params: dict) -> dict:
    url = item.get("url")
    if not url or "://" not in url:
        raise ValueError("Invalid URL")

    try:
        probe_url = f"{url.rstrip('/')}/api/health"
        response = requests.get(probe_url, timeout=5)
        return {"status": "reachable", "status_code": response.status_code, "response_time_ms": response.elapsed.total_seconds() * 1000}
    except requests.RequestException as e:
        return {"status": "unreachable", "error": str(e)}



actions = {
    "ping": handle_node_ping,
    "api_probe": handle_api_probe,
}
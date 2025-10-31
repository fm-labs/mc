import time
from pathlib import Path

from mc.config import DATA_DIR
from mc.db.mongodb import get_mongo_collection
from mc.util.autossh_util import setup_autossh_tunnel


if __name__ == "__main__":
    """
    Set up autossh tunnels for all hosts with SSH tunnel enabled.
    """
    print("[hoststunnel] Setting up autossh tunnels ...")

    host_collection = get_mongo_collection("inventory", "host")
    findings_collection = get_mongo_collection("findings", "findings")

    filters = {"properties.tunnel_enabled": True, "properties.ssh_enabled": True}
    hosts = host_collection.find(filters)
    for host in hosts:
        name = host.get("name", "")
        print("[hoststunnel] Processing host: " + name)

        props = host.get("properties", {})
        hostname = props.get("hostname")
        if not hostname:
            print("Skipping: no hostname defined")
            continue

        ssh_hostname = props.get("ssh_hostname", hostname)
        ssh_user = props.get("ssh_user", "")
        ssh_port = props.get("ssh_port", "22")
        ssh_key_name = props.get("ssh_key_name", "")
        if ssh_key_name:
            ssh_key_path = f"~/.ssh/{ssh_key_name}"

        # comma-separated list of tunnel forward specs
        # e.g. "L9001:localhost:2001,R9002:localhost:2002"
        tunnel_forward_specs_str = props.get("tunnel_forward_specs")
        tunnel_forward_specs = tunnel_forward_specs_str.split(";")
        # filter all specs, starting with L, strip the L
        tunnel_forward_specs_l = [spec[1:] for spec in tunnel_forward_specs if spec.startswith("L")]
        tunnel_forward_specs_r = [spec[1:] for spec in tunnel_forward_specs if spec.startswith("R")]

        pid_file = f"{DATA_DIR}/autossh/autossh_{hostname}.pid"
        Path(pid_file).parent.mkdir(parents=True, exist_ok=True)

        pid = setup_autossh_tunnel(
            remote_host=ssh_hostname,
            remote_user=ssh_user,
            pid_file=pid_file,
            local_forward_specs=tunnel_forward_specs_l,
            remote_forward_specs=tunnel_forward_specs_r,
            load_ssh_key=lambda: True
        )
        print(f"Autossh tunnel to {ssh_hostname} initialized with PID: {pid}")

        autossh_result = {
            "pid": pid,
            "pid_file": pid_file,
            "timestamp": int(time.time())
        }

        # store result of autossh tunnel setup in inventory meta data
        host_collection.update_one({"_id": host.get("_id")},
                                   {"$set": {"sshtunnel": autossh_result}})

        # create or update finding
        severity = 0  # "info"
        message = f"OK - SSH tunnel established (PID: {pid}) Ports: {tunnel_forward_specs_str}"

        if pid is None:
            severity = 3
            message = "ERROR - Failed to setup SSH tunnel"

        finding = {
            "resource_type": "host",
            "resource_id": str(host.get("_id")),
            "resource_name": host.get("name"),
            "check_name": "sshtunnel",
            "details": autossh_result,
            "severity": severity,
            "timestamp": int(time.time()),
            "message": message
        }
        findings_collection.update_one({
            "resource_type": "host",
            "resource_name": host.get("name"),
            "type": "sshtunnel"
        },
            {
                "$set": finding,
                "$setOnInsert": {"first_seen": int(time.time())}
            }, upsert=True)

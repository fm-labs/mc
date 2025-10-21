from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Query, HTTPException
from paramiko.client import SSHClient
from rx.helper.sshpy_helper import ssh_connect
from starlette.requests import Request
from starlette.responses import StreamingResponse

from mc.db.mongodb import mongodb_results_to_json
from mc.inventory.storage import get_inventory_storage_instance
from mc.util.ssh_async import stream_exec_command

router = APIRouter()

@router.get("/infrastructure/host/{host_id}/services")
def get_infrastructure_host_services(host_id: str) -> list:
    """
    Get related inventory items for a given inventory host
    """
    db = get_inventory_storage_instance()
    host = db.get_item("host", host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host_name = host.get("name")
    if not host_name:
        raise HTTPException(status_code=400, detail="Host has no name")

    all_compose_apps = db.list_items("compose_app")
    print(f"Found {len(all_compose_apps)} compose apps in inventory", all_compose_apps)
    related_items = []
    for app in all_compose_apps:
        print(app)
        app_target = app.get("properties", {}).get("target_url", "")
        if app_target == "ssh://" + host_name or app_target.endswith("@" + host_name):
            _app = app
            _app["status"] = "running"  # todo check status
            _app["item_type"] = "compose-project"
            related_items.append(app)

    #return mongodb_results_to_json(related_items)
    return related_items



@router.get("/infrastructure/host/{host_id}/system")
def get_infrastructure_host_system_info(host_id: str) -> dict:
    db = get_inventory_storage_instance()
    host = db.get_item("host", host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host_name = host.get("name")
    if not host_name:
        raise HTTPException(status_code=400, detail="Host has no name")

    client: SSHClient
    try:
        client = ssh_connect(host_name)
        print(f"Connected to {host_name}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    stdin, stdout, stderr = client.exec_command("systemctl list-units --type=service --all --no-pager --no-legend --plain --output=json")
    services = []
    for line in stdout:
        line = line.strip()
        if line:
            try:
                service = eval(line)  # Using eval here for simplicity; in production use json.loads
                services.append(service)
            except Exception as e:
                print(f"Failed to parse line: {line}, error: {e}")

    return {"services": services}


@router.get("/infrastructure/host/{host_id}/logs/stream")
def stream_ssh_host_logs(request: Request,
                                 host_id: str,
                                 log_type: Annotated[str, Query()] = "syslog", # auth, systemd, syslog, kernel
                                 since: Annotated[int, Query()] = None,
                                 until: Annotated[int, Query()] = None,
                                 tail: Annotated[int, Query()] = 1000,
                                 follow: Annotated[bool, Query()] = False,
                                 ) -> StreamingResponse:

    db = get_inventory_storage_instance()
    host = db.get_item("host", host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host_name = host.get("name")
    if not host_name:
        raise HTTPException(status_code=400, detail="Host has no name")

    kwargs: dict[str, Any] = {
        "stream": True,
        "follow": False, #todo follow,
    }
    if since:
        kwargs['since'] = since
    if until:
        kwargs['until'] = until
    if tail:
        kwargs['tail'] = tail
    if log_type not in ["syslog", "auth", "system", "kernel"]:
        raise HTTPException(status_code=400, detail="Invalid log type")
    kwargs['log_type'] = log_type

    # get log stream (blocking iterator)
    print(f"Opening log stream for host {host_name}")
    client: SSHClient
    try:
        client = ssh_connect(host_name)
        print(f"Connected to {host_name}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # return SSE response
    return StreamingResponse(
        ssh_host_logs_stream_sse(client, **kwargs),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


async def ssh_host_logs_stream(client: SSHClient, **kwargs) -> AsyncGenerator[tuple[str,str], None]:
    log_type = kwargs.get('log_type', 'syslog')
    since = kwargs.get('since')
    until = kwargs.get('until')
    tail = kwargs.get('tail', 1000)
    follow = kwargs.get('follow', False)
    sudo = kwargs.get('sudo', False)

    if log_type == "syslog":
        cmd = f"journalctl -q -n {tail}"
    elif log_type == "auth":
        cmd = f"journalctl -q -n {tail} _COMM=sshd"
    elif log_type == "systemd":
        cmd = f"journalctl -q -n {tail} _SYSTEMD_UNIT=systemd"
    elif log_type == "kernel":
        cmd = f"journalctl -q -n {tail} _TRANSPORT=kmsg"
    else:
        raise ValueError("Invalid log type")

    if since:
        cmd += f" --since @{since}"
    if until:
        cmd += f" --until @{until}"
    if follow:
        cmd += " -f"

    if sudo:
        cmd = "sudo -n " + cmd

    cmd += " --no-pager --output=short-iso"
    print(f"Executing command: {cmd}")

    # convert to async generator
    async for kind, payload in stream_exec_command(client, cmd, agent_forward=False):
        #print(f"[{kind}] {payload}", end="")
        #yield "data: " + payload + "\n\n"
        yield kind, payload


async def ssh_host_logs_stream_sse(client: SSHClient, **kwargs) -> AsyncGenerator[str, None]:
    async for kind, payload in ssh_host_logs_stream(client, **kwargs):
        yield "data: " + payload + "\n\n"

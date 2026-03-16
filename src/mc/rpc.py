# RPC handlers
import inspect
from typing import Callable, Any, Literal

from mc.util.random_util import generate_random_secret


def rpc_ping(**kwargs) -> dict:
    """
    A simple ping handler for testing connectivity.
    """
    return {"status": "success", "response": "pong", "received_params": kwargs}


def rpc_echo(message: str = None, **kwargs) -> dict:
    """
    A simple echo handler that returns the received parameters.
    """
    return {"status": "success", "response": f"You said: {message}", "received_params": kwargs}


def rpc_user_change_password(username: str, old_password, new_password: str, new_password2, **kwargs) -> dict:
    """
    Change a user's password. This is a wrapper around the users.change_password function.
    """
    from mc.users import change_password
    try:
        if new_password != new_password2:
            raise ValueError("New passwords do not match")

        change_password(username, old_password, new_password)
        return {"status": "success", "message": f"Password for user '{username}' has been changed."}
    except Exception as e:
        return {"error": str(e)}


def rpc_user_reset_password(username: str, **kwargs) -> dict:
    """
    Reset a user's password without checking the old one. This is a wrapper around the users.set_password function.
    The new password will be printed to the console, so only server administrators should have access to see this.
    """
    from mc.users import set_password
    try:
        new_password = generate_random_secret(32)
        set_password(username, new_password)
        print(f"Password for user '{username}' has been reset: {new_password}.")
        return {"status": "success", "message": f"Password for user '{username}' has been reset to a new random password."}
    except Exception as e:
        return {"error": str(e)}


def rpc_docker_info(**kwargs) -> dict:
    """
    Retrieve Docker system information using the Docker SDK for Python.
    """
    import docker
    client = docker.from_env()
    info = client.info()
    return {"status": "success", "data": info}


def rpc_self_update(**kwargs) -> dict:
    """
    Pull the latest image from the registry and restart the server.
    """
    import docker
    client = docker.from_env()
    image_name = "docker.io/fmlabs/mc:latest"
    try:
        print(f"Pulling latest image: {image_name}")
        client.images.pull(image_name)
        print("Image pulled successfully")
    except Exception as e:
        print(f"Error pulling image: {e}")
        return {"error": str(e)}
    return {"status": "success", "message": f"Image '{image_name}' pulled successfully. Please restart the server to apply the update."}


def rpc_container_action(container_id: str, action: Literal["start", "stop", "restart", "pause", "unpause"], **kwargs) -> dict:
    """
    Perform an action (start, stop, restart) on a Docker container.

    :param container_id: The ID or name of the Docker container.
    :param action: The action to perform ('start', 'stop', 'restart').
    """
    import docker
    client = docker.from_env()
    try:
        container = client.containers.get(container_id)
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop()
        elif action == "restart":
            container.restart()
        elif action == "pause":
            container.pause()
        elif action == "unpause":
            container.unpause()
        else:
            return {"error": f"Invalid action '{action}'. Valid actions are 'start', 'stop', 'restart'."}
        return {"status": "success", "message": f"Container '{container_id}' {action}ed successfully."}
    except Exception as e:
        return {"error": str(e)}


def rpc_docker_swarm_info(**kwargs) -> dict:
    """
    Retrieve Docker Swarm information using the Docker SDK for Python.
    """
    import docker
    client = docker.from_env()
    try:
        swarm_info = client.swarm.attrs
        return {"status": "success", "data": swarm_info}
    except Exception as e:
        return {"error": str(e)}


def rpc_docker_swarm_join_token(token_type: Literal["Worker", "Manager"], **kwargs) -> dict:
    """
    Retrieve the Docker Swarm join token for worker nodes.
    """
    import docker
    client = docker.from_env()
    try:
        swarm_info = client.swarm.attrs
        join_token = swarm_info.get("JoinTokens", {}).get(token_type)
        if not join_token:
            return {"error": "Swarm join token not found. Is this node part of a swarm?"}
        return {"status": "success", "join_token": join_token}
    except Exception as e:
        return {"error": str(e)}


def rpc_docker_swarm_init(advertise_addr: str|None = None, listen_addr: str = "0.0.0.0:2377", **kwargs) -> dict:
    """
    Initialize a Docker Swarm on this node.

    :param advertise_addr: The address to advertise to other swarm nodes (e.g., "10.30.1[:2377]").
    :param listen_addr: The address to listen on for swarm management traffic (e.g., "10.30.1:2377").
    """
    import docker
    client = docker.from_env()
    try:
        client.swarm.init(advertise_addr=advertise_addr, listen_addr=listen_addr)
        return {"status": "success", "message": "Swarm initialized successfully."}
    except Exception as e:
        return {"error": str(e)}


def rpc_docker_swarm_leave(force: bool = False, **kwargs) -> dict:
    """
    Leave the Docker Swarm on this node.

    :param force: If True, force the node to leave the swarm even if it is a manager.
    """
    import docker
    client = docker.from_env()
    try:
        client.swarm.leave(force=force)
        return {"status": "success", "message": "Swarm left successfully."}
    except Exception as e:
        return {"error": str(e)}


# RPC registry and dispatcher

RPC_HANDLERS = {
    # system handlers
    "ping": rpc_ping,
    "echo": rpc_echo,
    "self.update": rpc_self_update,
    # docker handlers
    "docker.info": rpc_docker_info,
    "docker.container.action": rpc_container_action,
    # swarm handlers
    "docker.swarm.info": rpc_docker_swarm_info,
    "docker.swarm.join_token": rpc_docker_swarm_join_token,
    "docker.swarm.init": rpc_docker_swarm_init,
    "docker.swarm.leave": rpc_docker_swarm_leave,
    # user handlers
    "user.change_password": rpc_user_change_password,
    "user.reset_password": rpc_user_reset_password,
}

def dispatch_rpc_method(method: str, params: dict) -> dict:
    handler = RPC_HANDLERS.get(method)
    if not handler:
        raise ValueError(f"Method '{method}' not found.")
    return handler(**params)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Python-type → JSON Schema type mapping (best-effort)
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}

def _params_from_signature(fn: Callable[..., Any]) -> dict:
    """Derive a minimal JSON-Schema ``parameters`` dict from a function signature."""
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls", "args", "kwargs"):
            continue
        prop: dict[str, Any] = {}
        annotation = param.annotation
        if annotation is not inspect.Parameter.empty:
            prop["type"] = _TYPE_MAP.get(annotation, "string")
        else:
            prop["type"] = "string"
        properties[name] = prop

        # if the annotation is a string literal (e.g. Literal["start", "stop", "restart"]), we can extract the possible values for better schema generation
        print(f"Processing parameter '{name}' with annotation", annotation)
        if hasattr(annotation, "__origin__") and annotation.__origin__ is Literal:
            prop["enum"] = annotation.__args__

        if name.endswith("password") or name.endswith("secret") or name.endswith("token"):
            prop["format"] = "password"

        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def rpc_schemas() -> list[dict]:
    """Generate JSON-Schema method definitions for all registered RPC handlers."""
    schemas: list[dict] = []
    for method_name, handler in RPC_HANDLERS.items():
        schemas.append({
            "method": method_name,
            "description": handler.__doc__ or "",
            "inputSchema": _params_from_signature(handler)
        })
    return schemas

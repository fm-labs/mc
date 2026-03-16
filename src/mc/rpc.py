# RPC handlers
import inspect
from typing import Callable, Any, Literal


def handle_ping(**kwargs) -> dict:
    """
    A simple ping handler for testing connectivity.
    """
    return {"status": "success", "response": "pong", "received_params": kwargs}


def handle_echo(**kwargs) -> dict:
    """
    A simple echo handler that returns the received parameters.
    """
    return {"status": "success", "response": "echo", "received_params": kwargs}


def handle_get_docker_info(**kwargs) -> dict:
    """
    Retrieve Docker system information using the Docker SDK for Python.

    :param params: A dictionary of parameters sent with the request (not used in this handler).
    """
    import docker
    client = docker.from_env()
    info = client.info()
    return {"status": "success", "data": info}


def handle_self_update(**kwargs) -> dict:
    """
    Pull the latest image from the registry and restart the server.
    """
    import docker
    client = docker.from_env()
    image_name = "docker.io/fm/mc:latest"
    try:
        print(f"Pulling latest image: {image_name}")
        client.images.pull(image_name)
        print("Image pulled successfully")
    except Exception as e:
        print(f"Error pulling image: {e}")
        return {"error": str(e)}
    return {"status": "success", "message": f"Image '{image_name}' pulled successfully. Please restart the server to apply the update."}


def handle_container_action(container_id: str, action: Literal["start","stop","restart","pause","unpause"], **kwargs) -> dict:
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


# RPC registry and dispatcher

RPC_HANDLERS = {
    # system handlers
    "ping": handle_ping,
    "echo": handle_echo,
    "self_update": handle_self_update,
    # docker handlers
    "docker.info": handle_get_docker_info,
    "docker.container_action": handle_container_action,
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

        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def rpc_method_schemas() -> dict[str, dict]:
    """Generate JSON-Schema method definitions for all registered RPC handlers."""
    schemas: dict[str, dict] = {}
    for method_name, handler in RPC_HANDLERS.items():
        schemas[method_name] = {
            "description": handler.__doc__ or "",
            "parameters": _params_from_signature(handler)
        }
    return schemas
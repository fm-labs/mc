

# RPC handlers

def handle_ping(params: dict) -> dict:
    return {"response": "pong", "received_params": params}


def handle_echo(params: dict) -> dict:
    return {"response": "echo", "received_params": params}


def handle_get_docker_info(params: dict) -> dict:
    import docker
    client = docker.from_env()
    info = client.info()
    return {"docker_info": info}



# RPC registry and dispatcher

RPC_HANDLERS = {
    "ping": handle_ping,
    "echo": handle_echo,
    "docker.info": handle_get_docker_info,
}

def dispatch_rpc_method(method: str, params: dict) -> dict:
    handler = RPC_HANDLERS.get(method)
    if not handler:
        raise ValueError(f"Method '{method}' not found.")
    return handler(params)

from fastapi import APIRouter

from mc.rpc import dispatch_rpc_method

router = APIRouter(prefix="/rpc", tags=["rpc"])


# RPC REST endpoint

@router.post("/execute")
def execute_json_rpc(request: dict) -> dict:
    """
    A simple JSON-RPC endpoint for executing commands.
    The request should be in the format:
    {
        "jsonrpc": "2.0",
        "method": "command_name",
        "params": { ... },
        "id": 1
    }
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        result = dispatch_rpc_method(method, params)
    except Exception as e:
        if request_id is None:
            return {}
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": str(e)},
            "id": request_id
        }

    if request_id is not None:
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
    # Notification, no response needed
    return {}

from fastapi import APIRouter
from starlette.requests import Request

from mc.config import API_VERSION, API_NAME, MC_MCP_ENABLED

router = APIRouter()

@router.get("/info", tags=["system"])
def info(req: Request) -> dict:
    hostname = req.headers.get("Host")
    origin = req.headers.get("Origin")

    return {
        "version": API_VERSION,
        "title": API_NAME,
        "mcp_enabled": MC_MCP_ENABLED,
        "mcp_url": "",
        "_host": hostname,
        "_origin": origin,
    }


@router.get("/health", tags=["system"])
def health():
    return {"status": "OK"}


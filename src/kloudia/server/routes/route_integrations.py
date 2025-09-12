from typing import List

from fastapi import APIRouter

from kloudia.config import load_config_json
from kloudia.config import save_config_json

router = APIRouter()

def fetch_integrations() -> List[dict]:
    return load_config_json("integrations")

@router.get("/")
async def list_integrations() -> List[dict]:
    return fetch_integrations()


@router.get("/{integration_id}")
async def get_integration(integration_id: str) -> dict:
    integrations = fetch_integrations()
    integration = None
    for integ in integrations:
        if integ.get("id") == integration_id:
            integration = integ
            break
    if not integration:
        return {"error": "Integration not found"}
    return integration


@router.post("/{integration_id}")
async def add_integration(integration_id: str, integration_data: dict) -> dict:
    integrations = fetch_integrations()
    for integ in integrations:
        if integ.get("id") == integration_id:
            return {"error": "Integration already exists"}
    integration_data["id"] = integration_id
    integrations.append(integration_data)
    save_config_json("integrations", integrations)
    return integration_data
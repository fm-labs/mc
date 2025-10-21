from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends
from fastapi.params import Body
from pydantic import BaseModel

from mc.integrations.helper import get_enabled_integrations, handle_integration_event, \
    is_integration_connected_for_user
from mc.server.auth import get_current_user

router = APIRouter()

class IntegrationModel(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    connected: bool = False

class IntegrationStatusModel(BaseModel):
    status: str
    integration: str
    details: Optional[dict] = None


@router.get("/integrations")
def list_integrations(current_user: dict = Depends(get_current_user)) -> List[IntegrationModel]:
    """
    List of available integrations.
    """
    enabled = get_enabled_integrations()
    user_integrations = []
    for integration in enabled:
        user_integrations.append(IntegrationModel(**{
            "name": integration["name"],
            "title": integration.get("title", integration["name"]),
            "description": integration.get("description", ""),
            "connected": is_integration_connected_for_user(integration["name"], current_user["username"]),
        }))
    return user_integrations


@router.post("/integrations/{name}/connect", response_model=IntegrationStatusModel)
def connect_integration(name: str,
                        current_user: dict = Depends(get_current_user),
                        data: Annotated[dict, Body()] = None) -> IntegrationStatusModel:
    """
    Connect to an integration.
    """
    result = handle_integration_event("connect", name, current_user["username"], data)
    return IntegrationStatusModel(**result)


@router.get("/integrations/{name}/status", response_model=IntegrationStatusModel)
def get_integration_status(name: str,
                           current_user: dict = Depends(get_current_user)) -> IntegrationStatusModel:
    """
    Get the status of an integration.
    """
    result = handle_integration_event("status", name, current_user["username"], {})
    return IntegrationStatusModel(**result)


@router.post("/integrations/{name}/disconnect", response_model=IntegrationStatusModel)
def disconnect_integration(name: str,
                           current_user: dict = Depends(get_current_user)) -> IntegrationStatusModel:
    """
    Disconnect from an integration.
    """
    result = handle_integration_event("disconnect", name, current_user["username"], {})
    return IntegrationStatusModel(**result)

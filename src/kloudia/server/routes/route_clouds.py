from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from kloudia.config import load_config_json
from kloudia.tasks import scan_cloud_task

class KloudiaAwsAccountModel(BaseModel):
    account_id: str
    regions: List[str]

class KloudiaGcpAccountModel(BaseModel):
    project_id: str
    regions: List[str]

class KloudiaAzureAccountModel(BaseModel):
    subscription_id: str
    regions: List[str]

class KloudiaCloudModel(BaseModel):
    name: str
    platform: str
    aws: KloudiaAwsAccountModel = None
    gcp: KloudiaGcpAccountModel = None
    azure: KloudiaAzureAccountModel = None


router = APIRouter()

def fetch_clouds() -> List[dict]:
    return load_config_json("clouds")

@router.get("/")
async def get_clouds() -> List[KloudiaCloudModel]:
    return [KloudiaCloudModel(**cloud) for cloud in fetch_clouds()]


@router.get("/{cloud_name}", response_model=KloudiaCloudModel)
async def get_cloud(cloud_name: str) -> KloudiaCloudModel:
    clouds = fetch_clouds()
    for cloud in clouds:
        if cloud["name"] == cloud_name:
            return KloudiaCloudModel(**cloud)
    return None

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from kloudia.config import load_config_json


class KloudiaFindingModel(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    resource: str
    region: str
    cloud_provider: str

router = APIRouter()

def fetch_findings() -> List[dict]:
    return load_config_json("findings_example")


@router.get("/")
async def get_findings() -> List[KloudiaFindingModel]:
    return [KloudiaFindingModel(**finding) for finding in fetch_findings()]


from typing import List

from fastapi import APIRouter

from kloudia.config import load_config_json
from kloudia.inventory.repos.datamodels import KloudiaRepoModel

router = APIRouter()

def fetch_repos() -> List[dict]:
    return load_config_json("repos")

@router.get("/")
async def get_repos() -> List[KloudiaRepoModel]:
    return [KloudiaRepoModel(**repo) for repo in fetch_repos()]


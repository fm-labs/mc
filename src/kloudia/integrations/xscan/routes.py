from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from kloudia.config import load_config_json
from kloudia.tasks import scan_cloud_task, scan_repo_task, scan_domain_task

class KloudiaScanResultModel(BaseModel):
    id: str
    tool: str
    tool_version: str
    artifacts: List[str]
    status: str
    message: str
    started_at: str
    finished_at: str | None = None

router = APIRouter()

def fetch_scan_results(category: str, target: str) -> List[dict]:
    return load_config_json("scan_results_example")


@router.get("/xscan/results/{category}/{target}", response_model=KloudiaScanResultModel)
async def get_scan_results(category: str, target: str) -> List[KloudiaScanResultModel]:
    return [KloudiaScanResultModel(**result) for result in fetch_scan_results(category, target)]


@router.post("/xscan/run/{category}/{target}")
async def run_domain_scan(category: str, target: str):
    if category == "cloud":
        task = scan_cloud_task.delay(target)
    elif category == "repo":
        task = scan_repo_task.delay(target)
    elif category == "domain":
        task = scan_domain_task.delay(target)
    else:
        return {"error": "Invalid scan category."}
    return {"task_id": task.id, "status": "started"}
import uuid
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from kloudia.config import load_config_json
from kloudia.tasks import task_scan_cloud, task_scan_repo, task_scan_domain

class KloudiaScanConfigModel(BaseModel):
    mode: str
    target: str

class KloudiaScanResultModel(BaseModel):
    uuid: str
    tool: str
    tool_version: str
    artifacts: List[str]
    status: str
    message: str
    started_at: str
    finished_at: str | None = None

router = APIRouter()

def fetch_scan_results(scan_id) -> List[dict]:
    all_results = load_config_json("scan_results_example")
    return [result for result in all_results if result["uuid"] == scan_id]


@router.get("/xscan/{scan_id}", response_model=KloudiaScanResultModel)
async def get_scan_results(uuid: str) -> KloudiaScanResultModel | dict:
    """
    Retrieve scan results by scan ID.
    """
    result = fetch_scan_results(uuid)
    if not result:
        return {"error": "Scan not found."}, 404
    return KloudiaScanResultModel(**result[0])


@router.post("/xscan/run")
async def run_domain_scan(request: KloudiaScanConfigModel) -> dict:
    mode = request.mode
    target = request.target
    scan_id = str(uuid.uuid4())

    if mode == "cloud":
        task = task_scan_cloud.delay(target, ref=scan_id)
    elif mode == "repo":
        task = task_scan_repo.delay(target, ref=scan_id)
    elif mode == "domain":
        task = task_scan_domain.delay(target, ref=scan_id)
    else:
        return {"error": "Invalid scan category."}

    return {"scan_id": scan_id, "task_id": task.id, "status": "queued"}
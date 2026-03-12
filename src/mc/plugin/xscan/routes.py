import asyncio
import inspect
from typing import List

from fastapi import APIRouter
from fastapi import Request
from fastapi import Query
from fastapi import Depends
from pydantic import BaseModel

from mc.plugin.xscan.helper import fetch_scan_result

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


@router.get("/xscan/results/{scan_id}", response_model=KloudiaScanResultModel)
async def get_xscan_results(uuid: str) -> KloudiaScanResultModel | dict:
    """
    Retrieve scan results by scan ID.
    """
    result = fetch_scan_result(uuid)
    if not result:
        return {"error": "Scan not found."}, 404
    return KloudiaScanResultModel(**result[0])


# @router.post("/xscan/run")
# async def submit_xscan_request(request: KloudiaScanConfigModel) -> dict:
#     mode = request.mode
#     target = request.target
#
#     return init_scan(mode, target)



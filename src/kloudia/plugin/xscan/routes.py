import asyncio
import inspect
from typing import List

from fastapi import APIRouter
from fastapi import Request
from fastapi import Query
from fastapi import Depends
from pydantic import BaseModel

from kloudia.plugin.xscan.helper import fetch_scan_result

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




@router.get("/xscan/webcheck/{check_name}")
async def get_webcheck_results(check_name: str, url: str=None) -> dict:
    """
    Retrieve scan results by scan ID.
    """
    # get url parameter from query string
    # e.g. /xscan/webcheck/{check_name}?url=http://example.com
    if not url:
        return {"error": "URL parameter is required."}

    if check_name in ["cookies", "threats", "screenshot", "tls"]:
        return {"error": "Check is currently disabled globally."}

    ckeck_module = check_name #.replace("-", "_")
    module_name = "xscan.domain.webcheck." + ckeck_module
    # load the "handler" function from the module
    # and invoke with url as parameter
    try:
        module = __import__(module_name, fromlist=["handler"])
        h = getattr(module, "handler")

        # handler can be async or sync
        if inspect.iscoroutinefunction(h):
            out = await asyncio.wait_for(
                h(url), timeout=30
            )
        else:
            # run blocking handler in a thread so it can't block the loop
            out = await asyncio.wait_for(
                asyncio.to_thread(h, url),
                timeout=30,
            )

        #return {"check_name": check_name, "result": out}
        return out
    except (ImportError, AttributeError) as e:
        return {"error": "Check not found: " + str(e)}
    except Exception as e:
        return {"error": str(e)}

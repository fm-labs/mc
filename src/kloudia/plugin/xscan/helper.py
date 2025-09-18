import json
from pathlib import Path
from time import time

from xscan.model import ScanResult, ScanConfig

from kloudia.config import DATA_DIR


# def init_scan(mode: str, target: str):
#     scan_id = uuid.uuid4().hex
#     #scan_config = ScanConfig(mode, target, ref=scan_id, output_dir=f"/data/xscan/{scan_id}")
#
#     if mode == "cloud":
#         task = task_scan_cloud.delay(target, ref=scan_id)
#     elif mode == "repo":
#         task = task_scan_repo.delay(target, ref=scan_id)
#     elif mode == "image":
#         task = task_scan_container_image.delay(target, ref=scan_id)
#     elif mode == "domain":
#         task = task_scan_domain.delay(target, ref=scan_id)
#     else:
#         return {"error": "Invalid scan category."}
#
#     return {"scan_id": scan_id, "task_id": task.id, "status": "queued"}


def parse_scan_result(scan_result: ScanResult) -> dict:
    return {
        "mode": scan_result.mode,
        "target": scan_result.target,
        "findings": scan_result.findings,
        "artifacts": scan_result.artifacts,
        #"started_at": str(scan_result.started_at),
        "finished_at": int(time()), #str(scan_result.finished_at),
        "status": "completed",
        "issues_found": len(scan_result.findings),
    }


def store_scan_result(scan_id: str, result: dict):
    print(f"Storing scan result for {scan_id}", result)
    outdir = f"{DATA_DIR}/scan_results/{scan_id}"
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)
    result_file = outpath / "result.json"
    with result_file.open("w") as f:
        json.dump(result, f, indent=2)


def fetch_scan_result(scan_id) -> dict | None:
    print(f"Fetching scan result for {scan_id}")
    outdir = f"{DATA_DIR}/scan_results/{scan_id}"
    outpath = Path(outdir)
    result_file = outpath / "result.json"
    if not result_file.exists():
        return None
    with result_file.open("r") as f:
        return json.load(f)


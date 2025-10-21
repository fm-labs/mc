from pathlib import Path
import json

from mc.util.fs_util import list_files_in_dir_recursive
from orchestra.celery import celery

from orchestra.settings import DATA_DIR


# @celery.task
# def task_scan_repo(repo_name: str, ref: str = None):
#     output_dir = f"{DATA_DIR}/xscan/{ref}"
#     scan = ScanConfig("repo", repo_name, ref=ref, output_dir=output_dir)
#     print(f"Init repo scan: {scan}")
#
#     try:
#         runner = RepoScanRunner()
#         scan_result = runner.execute_scan(scan)
#     except Exception as e:
#         print(f"Error during repo scan: {e}")
#         return {"error": str(e)}
#
#     result = parse_scan_result(scan_result)
#     store_scan_result(ref, result)
#     return result
#
#
# @celery.task
# def task_scan_container_image(image_name: str, ref: str = None):
#     output_dir = f"{DATA_DIR}/xscan/{ref}"
#     scan = ScanConfig("image", image_name, ref=ref, output_dir=output_dir)
#     print(f"Init image scan: {scan}")
#     try:
#         runner = ImageScanRunner()
#         scan_result = runner.execute_scan(scan)
#     except Exception as e:
#         print(f"Error during image scan: {e}")
#         return {"error": str(e)}
#
#     result = parse_scan_result(scan_result)
#     store_scan_result(ref, result)
#     return result
#
#
# @celery.task
# def task_scan_cloud(cloud_name: str, ref: str = None):
#     # Placeholder for scanning logic
#     print(f"Scanning cloud: {cloud_name}")
#     sleep(10)  # Simulate a time-consuming scan
#     scan_result = {"cloud_name": cloud_name, "status": "completed", "issues_found": 0}
#     return scan_result
#
#
# @celery.task
# def task_scan_domain(domain_name: str, ref: str = None):
#     # Placeholder for scanning logic
#     print(f"Scanning domain: {domain_name}")
#     sleep(10)  # Simulate a time-consuming scan
#     scan_result = {"domain_name": domain_name, "status": "completed", "issues_found": 0}
#     return scan_result


@celery.task
def task_parse_scan_result(ref: str, result_dir: str):
    # Read the results.json
    result_file = Path(result_dir) / "result.json"
    if not result_file.exists():
        print(f"Result file not found: {result_file}")
        return {"error": "Result file not found"}

    with open(result_file, "r") as f:
        scan_result = json.load(f)



    return scan_result
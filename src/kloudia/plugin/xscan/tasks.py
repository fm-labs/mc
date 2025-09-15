from time import sleep

from orchestra.celery import celery
from xscan.repo.runner import RepoScanRunner
from xscan.model import ScanConfig


@celery.task
def task_scan_repo(repo_name: str, ref: str = None):
    scan = ScanConfig("repo", repo_name, ref=ref)
    print(f"Init repo scan: {scan}")

    try:
        runner = RepoScanRunner()
        scan_result = runner.execute_scan(scan)
    except Exception as e:
        print(f"Error during repo scan: {e}")
        return {"error": str(e)}

    result = {
        "ref": ref,
        "target": repo_name,
        "findings": scan_result.findings,
        "artifacts": scan_result.artifacts,
        "started_at": str(scan_result.started_at),
        "finished_at": str(scan_result.finished_at),
        "status": "completed",
        "issues_found": len(scan_result.findings),
    }

    # todo store result in db or file system
    return result


@celery.task
def task_scan_cloud(cloud_name: str, ref: str = None):
    # Placeholder for scanning logic
    print(f"Scanning cloud: {cloud_name}")
    sleep(10)  # Simulate a time-consuming scan
    scan_result = {"cloud_name": cloud_name, "status": "completed", "issues_found": 0}
    return scan_result


@celery.task
def task_scan_domain(domain_name: str, ref: str = None):
    # Placeholder for scanning logic
    print(f"Scanning domain: {domain_name}")
    sleep(10)  # Simulate a time-consuming scan
    scan_result = {"domain_name": domain_name, "status": "completed", "issues_found": 0}
    return scan_result
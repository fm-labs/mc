from time import sleep

from orchestra.celery import celery

from xscan.runner import ScanRunner

from xscan.xscan import ScanRequest
from xscan.scanner.repo_scanner import TrivyRepoScanner

@celery.task
def scan_repo_task(repo_name: str):
    print(f"Scanning repository: {repo_name}")

    scanners = [
        TrivyRepoScanner
    ]

    scan = ScanRequest("repo", repo_name)
    print(f"Init repo scan: {scan}")

    runner = ScanRunner(scanners=scanners)
    _scan = runner.execute_scan(scan)

    scan_result = {"repo_name": repo_name, "status": "completed", "issues_found": len(_scan.findings)}
    return scan_result


@celery.task
def scan_cloud_task(cloud_name: str):
    # Placeholder for scanning logic
    print(f"Scanning cloud: {cloud_name}")
    sleep(10)  # Simulate a time-consuming scan
    scan_result = {"cloud_name": cloud_name, "status": "completed", "issues_found": 0}
    return scan_result


@celery.task
def scan_domain_task(domain_name: str):
    # Placeholder for scanning logic
    print(f"Scanning domain: {domain_name}")
    sleep(10)  # Simulate a time-consuming scan
    scan_result = {"domain_name": domain_name, "status": "completed", "issues_found": 0}
    return scan_result
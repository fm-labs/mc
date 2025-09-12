from orchestra.celery import celery

@celery.task
def example_task(x, y):
    return x + y


@celery.task
def sleep_task(duration: int):
    import time
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


@celery.task
def scan_repo_task(repo_name: str):
    # Placeholder for scanning logic
    print(f"Scanning repository: {repo_name}")
    # Simulate scan result
    scan_result = {"repo_name": repo_name, "status": "completed", "issues_found": 0}
    return scan_result


@celery.task
def scan_cloud_task(cloud_name: str):
    # Placeholder for scanning logic
    print(f"Scanning cloud: {cloud_name}")
    # Simulate scan result
    scan_result = {"cloud_name": cloud_name, "status": "completed", "issues_found": 0}
    return scan_result


@celery.task
def scan_domain_task(domain_name: str):
    # Placeholder for scanning logic
    print(f"Scanning domain: {domain_name}")
    # Simulate scan result
    scan_result = {"domain_name": domain_name, "status": "completed", "issues_found": 0}
    return scan_result
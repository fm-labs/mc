from mc.plugin.containers.compose_runner import LocalDockerComposeStackRunner, RemoteDockerComposeStackRunner
from orchestra.celery import celery

@celery.task(bind=True)
def task_deploy_compose_stack(self, project_name: str, project_dir: str, stackfile: str|list, host_url: str):
    if host_url.startswith("unix://"):
        compose_runner = LocalDockerComposeStackRunner(
            project_name=project_name,
            local_dir=project_dir,
            stackfile=stackfile,
            docker_host=host_url
        )
    elif host_url.startswith("ssh://"):
        compose_runner = RemoteDockerComposeStackRunner(
            project_name=project_name,
            local_dir=project_dir,
            stackfile=stackfile,
            docker_host=host_url
        )
    else:
        raise ValueError(f"Unsupported host URL scheme: {host_url}")

    compose_runner.stop()
    compose_runner.sync()

    stdout, stderr, rc = compose_runner.up()
    return {"status": "success",
            "message": f"App {project_name} deployed to {host_url}",
            "stdout": stdout.decode(), "stderr": stderr.decode(), "return_code": rc}


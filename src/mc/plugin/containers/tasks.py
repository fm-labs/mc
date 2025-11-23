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


# def deploy_compose_project_to_container_host(host_url: str, app_name: str, app_dir: str, compose_args: dict = None) -> dict:
#     """
#     :deprecated:
#     """
#
#     print(f"Deploying compose project '{app_name}' from dir {app_dir} to host '{host_url}'")
#     if compose_args is None:
#         compose_args = {}
#     ssh_args = ssh_params_from_url(host_url)
#
#     run_cfg = RunConfig(
#         src=f"file://{app_dir}",
#         dest=host_url,
#         extra={
#             "ssh": ssh_args,
#             "compose": compose_args,
#             "exclude": ".dockerignore" # exclude PATTERNS from .dockerignore file, if exists
#         }
#     )
#     ctx = GlobalContext(
#         config_path=Path(app_dir) / "rx.yaml",
#         cwd=Path(app_dir),
#         dry_run=False,
#         config=Config(
#             metadata=Metadata(name=app_name, version="0.1.0", description=f""),
#             variables={},
#             build={},
#             run={}
#         ),
#     )
#     stdout, stderr, rc = handle_docker_compose_run(run_cfg, ctx)
#     return {"status": "success",
#             "message": f"App {app_name} deployed to {host_url}",
#             "stdout": stdout, "stderr": stderr, "return_code": rc}
#

from pathlib import Path

from rx.config import RunConfig, GlobalContext, Config, Metadata

from rx.plugin.docker_compose import handle_docker_compose_run, ssh_params_from_url


def deploy_compose_project_to_container_host(host_url: str, app_name: str, app_dir: str):

    print(f"Deploying compose project '{app_name}' from dir {app_dir} to host '{host_url}'")

    ssh_args = ssh_params_from_url(host_url)
    compose_args = {}
    # compose file is assumed to be in the app_dir
    # compose_args["composefile"] = str(Path(app_dir) / "compose.yaml")
    # look for traefik or override files

    run_cfg = RunConfig(
        src=f"file://{app_dir}",
        dest=host_url,
        extra={
            "ssh": ssh_args,
            "compose": compose_args
        }
    )
    ctx = GlobalContext(
        config_path=Path(app_dir) / "rx.yaml",
        cwd=Path(app_dir),
        dry_run=False,
        config=Config(
            metadata=Metadata(name=app_name, version="0.1.0", description=f""),
            variables={},
            build={},
            run={}
        ),
    )
    handle_docker_compose_run(run_cfg, ctx)

    return {"status": "success", "message": f"App {app_name} deployed to {host_url}"}

from pathlib import Path

from rx.config import RunConfig, GlobalContext, Config, Metadata

from kloudia.config import RESOURCES_DIR
from rx.plugin.docker_compose import handle_docker_compose_run, ssh_params_from_url


def deploy_template_to_container_host(host_url: str, template_name: str, template_args: dict):

    template_dir_path = Path(RESOURCES_DIR) / "compose-templates" / template_name
    if not template_dir_path.exists() or not template_dir_path.is_dir():
        raise FileNotFoundError(f"{template_dir_path} does not exist")

    project_name = template_args.get("project_name", template_name)

    # lookup host in inventory
    #inventory = get_inventory_storage_instance()
    #host = inventory.get_item_by_key("container-hosts", gen_inventory_key(host_url))
    #if host is None:
    #    raise ValueError(f"Container host {host_url} not found in inventory")

    # lookup credentials for the host
    # ssh_credentials = get_ssh_credentials_for_host(host_url)

    ssh_args = ssh_params_from_url(host_url)
    compose_args = {}

    run_cfg = RunConfig(
        src="file://",
        dest=host_url,
        extra={
            "ssh": ssh_args,
            "compose": compose_args
        }
    )
    ctx = GlobalContext(
        config_path=template_dir_path / "rx.yaml",
        cwd=template_dir_path,
        dry_run=False,
        config=Config(
            metadata=Metadata(name=project_name, version="0.1.0", description=f"Created from template {template_name}"),
            variables={},
            build={},
            run={}
        ),
    )
    handle_docker_compose_run(run_cfg, ctx)

    return {"status": "success", "message": f"Template {template_name} deployed to {host_url}"}

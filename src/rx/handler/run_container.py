
from rx.config import RunConfig, GlobalContext
from rx.plugin.docker import handle_docker_container_run as docker_run_handler


def delegate_container_run(run_cfg: RunConfig, ctx: GlobalContext):
    # for now just delegate to docker handler
    # todo - implement podman handler
    return docker_run_handler(run_cfg, ctx)


handler = delegate_container_run

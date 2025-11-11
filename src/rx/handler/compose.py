from rx.config import RunConfig, GlobalContext
from rx.plugin.docker_compose import handle_docker_compose_run as docker_compose_run_handler


def delegate_compose_run(run_cfg: RunConfig, ctx: GlobalContext):
    # for now just delegate to docker handler
    # todo - implement podman handler
    return docker_compose_run_handler(run_cfg, ctx)


handler = delegate_compose_run


from rx.config import RunConfig, GlobalContext
from rx.plugin.docker import handle_docker_image_push as docker_publish_handler
#from rx.plugin.podman import handle_publish_image as podman_publish_handler
from rx.util import split_url

AVAILABLE_IMAGE_HANDLERS = {
    "dockerhub": docker_publish_handler,
    "ghcr": docker_publish_handler,
    "ecr": docker_publish_handler,
    "acr": docker_publish_handler,
    "quay": docker_publish_handler,
    "docker+dockerhub": docker_publish_handler,
    "docker+ghcr": docker_publish_handler,
    "docker+ecr": docker_publish_handler,
    "docker+acr": docker_publish_handler,
    "docker+quay": docker_publish_handler,
    "podman+dockerhub": docker_publish_handler,
    #"podman+ghcr": podman_publish_handler,
    #"podman+ecr": podman_publish_handler,
    #"podman+acr": podman_publish_handler,
    #"podman+quay": podman_publish_handler,
}

def handle_publish_image(run_cfg: RunConfig, ctx: GlobalContext):
    action = run_cfg.action
    src = run_cfg.src
    dest = run_cfg.dest

    if action != "publish-image":
        raise ValueError(f"Unsupported run type: {action}")

    [dschema, _] = split_url(dest)
    #if dschema not in SUPPORTED_IMAGE_REGISTRIES:
    #    raise ValueError(f"Unsupported image target schema: {dschema}")
    #[tool_name, registry_name] = dschema.split("+")  # handle tool+registry format

    _handler = AVAILABLE_IMAGE_HANDLERS.get(dschema)
    if not _handler:
        raise ValueError(f"No handler found for image target schema: {dschema}")
    return _handler(run_cfg, ctx)


handler = handle_publish_image

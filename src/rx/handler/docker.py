import os

from rx.config import RunConfig, GlobalContext
from rx.helper.awscli_helper import awscli_ecr_login
from rx.helper.dockercli_helper import dockercli_login
from rx.util import toolcmd
from rx.helper.subprocess_helper import rx_subprocess
from rx.util import parse_image_ref, split_url

DEFAULT_DOCKER_REGISTRY = "docker.io"
SUPPORTED_DOCKER_REGISTRIES = ["docker.io", "ghcr.io", "amazonaws.com", "azurecr.io",
                               "quay.io", "gcr.io", "registry.gitlab.com"]


def _get_credentials_aws(registry_url: str) -> tuple[str, str]:
    """
    https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry_auth.html
    aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com

    :param registry_url:
    :return:
    """
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", None)
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    profile = os.environ.get("AWS_PROFILE", None)
    region = os.environ.get("AWS_REGION", "us-east-1")

    ecr_url, ecr_username, ecr_password = awscli_ecr_login(ecr_url=registry_url,
                                            region=region,
                                            profile=profile,
                                            access_key=access_key,
                                            secret_key=secret_key)
    return ecr_username, ecr_password

def _get_credentials_acr() -> tuple[str, str]:
    username = os.environ.get("ACR_USERNAME", "")
    password = os.environ.get("ACR_PASSWORD", "")
    return username, password

def _get_credentials_dockerhub() -> tuple[str, str]:
    username = os.environ.get("DOCKERHUB_USERNAME", "")
    password = os.environ.get("DOCKERHUB_TOKEN", "")
    return username, password

def _get_credentials_ghcr():
    username = os.environ.get("GHCR_USERNAME", "")
    password = os.environ.get("GHCR_TOKEN", "")
    return username, password


def _get_container_registry_credentials(registry: str) -> tuple[str, str]:
    #username = ""
    #password = ""
    #return username, password

    if registry in ["docker.io", "index.docker.io", ""]:
        return _get_credentials_dockerhub()
    elif registry in ["ghcr.io"]:
        return _get_credentials_ghcr()
    elif registry.endswith("amazonaws.com"):
        return _get_credentials_aws(registry)
    elif registry.endswith("azurecr.io"):
        return _get_credentials_acr()
    else:
        # raise ValueError(f"Unsupported registry for docker login: {registry}")
        print(f"Warning: No credentials found for registry: {registry}. Attempting anonymous login.")
        return "",""


def docker_login(registry: str, env: dict = None):
    if registry is None or registry == "":
        registry = "docker.io"

    username, password = _get_container_registry_credentials(registry)
    if not username or not password:
        print(f"Warning: No credentials found for registry: {registry}. Attempting anonymous login.")
        return

    dockercli_login(username, password, registry, env=env)




def build_image_name_from_url(dest: str) -> str:
    [dscheme, dpath] = split_url(dest)
    #if dscheme not in SUPPORTED_DOCKER_REGISTRIES:
    #    raise ValueError(f"Unsupported image target schema: {dscheme}")

    # return as-is for http/https schemes
    if dscheme == "http" or dscheme == "https":
        return dest

    # inject registry domains for known registries
    if dscheme is None or dscheme == "" or dscheme == "dockerhub":
        dpath = f"docker.io/{dpath}"
    elif dscheme == "ghcr":
        dpath = f"ghcr.io/{dpath}"
    elif dscheme == "ecr":
        if not dpath.endswith(".amazonaws.com"):
            raise ValueError(f"ECR image must include registry domain, e.g., '123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:tag'")
    elif dscheme == "acr":
        if not dpath.endswith(".azurecr.io"):
            raise ValueError(f"ACR image must include registry domain, e.g., 'myregistry.azurecr.io/my-repo:tag'")
    elif dscheme == "quay":
        dpath = f"quay.io/{dpath}"
    elif dscheme == "gcr":
        dpath = f"gcr.io/{dpath}"
    elif dscheme == "gitlab":
        dpath = f"registry.gitlab.com/{dpath}"
    else:
        print(f"Warning: Unknown Docker image scheme: {dscheme}")

    return dpath


def _init_container_env(run_cfg: RunConfig, login=False):
    action = run_cfg.action  # should be "container"
    if action != "container":
        raise ValueError(f"Unsupported container run type: {action}")
    src = run_cfg.src  # source container image
    dest = run_cfg.dest  # destination runtime environment or host

    # validate the source container
    if not src:
        raise ValueError("Source image is required for container run.")
    if not dest:
        raise ValueError("Destination is required for container run.")

    # validate the destination scheme
    #[_dscheme, _] = split_url(dest)
    #if _dscheme not in AVAILABLE_IMAGE_HANDLERS.keys():
    #    raise ValueError("Destination scheme must be one of: " + ", ".join(AVAILABLE_IMAGE_HANDLERS.keys()))

    # build the docker environment
    # this includes DOCKER_HOST, DOCKER_CONFIG, etc.
    def build_docker_env(run_cfg: RunConfig) -> dict:
        dest = run_cfg.dest
        # default to local docker daemon
        if dest == "docker://" or dest == "local://":
            dest = "unix:///var/run/docker.sock"

        docker_cfg = run_cfg.extra.get("docker", {})
        env = docker_cfg.get("env", {})
        env["DOCKER_HOST"] = dest
        env["DOCKER_CONFIG"] = os.environ.get("DOCKER_CONFIG", "")
        # env["DOCKER_TLS_VERIFY"] = ""
        # env["DOCKER_CERT_PATH"] = ""
        return env
    env = build_docker_env(run_cfg)

    if login:
        try:
            [scheme, registry, port, namespace, image, tag, digest] = parse_image_ref(src)
            docker_login(registry, env=env)
        except Exception as e:
            print(f"Warn: Failed to get credentials or login to registry: {e}")
            # raise e
    return env


def _init_image_env(run_cfg: RunConfig, login=False):
    action = run_cfg.action  # should be "image"
    if action != "publish-image":
        raise ValueError(f"Unsupported image run type: {action}")
    src = run_cfg.src  # source image image
    dest = run_cfg.dest  # destination image registry repository

    # validate the source image
    if not src:
        raise ValueError("Source image is required for image run.")
    if not dest:
        raise ValueError("Destination is required for image run.")

    # todo validate the destination scheme
    # build the docker environment
    env = {}
    env["DOCKER_CONFIG"] = os.environ.get("DOCKER_CONFIG", "")

    if login:
        try:
            [scheme, registry, port, namespace, image, tag, digest] = parse_image_ref(dest)
            docker_login(registry, env=env)
        except Exception as e:
            print(f"Warn: Failed to get credentials or login to registry: {e}")
            raise e
    return env


def handle_docker_container_run(run_cfg: RunConfig, ctx: GlobalContext):
    env = _init_container_env(run_cfg, login=True)

    docker_cfg = run_cfg.extra.get("docker", {})
    # run the container
    docker_args = []
    run_args = docker_cfg.get("run_args", [])
    docker_args.extend(run_args)
    #if scheme in ["local"]:
    #    docker_cmd += ["--pull", "never"]

    docker_cmd = toolcmd("docker", ["run", "-d", "--rm"] + docker_args)
    # strip the scheme from the url
    docker_cmd += [split_url(run_cfg.src)[1]]
    return rx_subprocess(docker_cmd, cwd=ctx.cwd, env=env)



def handle_docker_image_push(run_cfg: RunConfig, ctx: GlobalContext):
    src = run_cfg.src # source image
    dest = run_cfg.dest # destination image

    # tag the src image to the dest image
    src_image = build_image_name_from_url(src)
    dest_image = build_image_name_from_url(dest)

    # login
    env = _init_image_env(run_cfg, login=True)

    # tag
    docker_cmd = toolcmd("docker", ["tag", src_image, dest_image])
    rx_subprocess(docker_cmd, cwd=ctx.cwd, env=env)

    # push
    docker_cmd = toolcmd("docker", ["push", dest_image])
    return rx_subprocess(docker_cmd, cwd=ctx.cwd, env=env)


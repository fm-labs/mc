import json
import os
from dataclasses import dataclass
from pathlib import Path

import dotenv
import yaml

from mc.config import DATA_DIR
from mc.plugin.containers.tasks import deploy_compose_project_to_container_host
from mc.plugin.rx.tasks import update_project_from_git


@dataclass(frozen=True)
class ComposeAppItem:
    name: str
    app_dir: str
    project_name: str
    description: str | None = None
    version: str | None = None
    source_url: str | None = None
    target_url: str | None = None  # e.g. ssh://user@host
    template_url: str | None = None  # e.g. git://user/repo
    domain_name: str | None = None  # optional domain name for the app
    traefik_enabled: bool = False  # whether to auto-wire traefik labels
    traefik_network_name: str | None = None  # name of the docker network traefik is on
    traefik_container_port: int | None = None  # port the app listens on, for traefik routing
    traefik_ssl_enabled: bool = False  # whether to enable SSL (https) for the app

    def __post_init__(self):
        if self.name is None or self.name == "":
            raise ValueError("ComposeAppItem 'name' cannot be empty")
        if self.app_dir is None or self.app_dir == "":
            raise ValueError("ComposeAppItem 'app_dir' cannot be empty")
        if self.project_name is None or self.project_name == "":
            raise ValueError("ComposeAppItem 'project_name' cannot be empty")

    # def __str__(self) -> str:
    #    return f"ComposeAppItem(name={self.name}, app_dir={self.app_dir}, project_name={self.project_name}, version={self.version})"

    def compile(self):
        print("Compiling ComposeAppItem '{}'".format(self.name))
        pass


def _build_app_dir_path(project_name: str, app_name: str) -> Path:
    base_dir = Path(f"data/projects/{project_name}/apps")
    app_dir = base_dir / app_name
    return app_dir


def _generate_random_secret(length: int = 32) -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def handle_compose_project_deploy(item: dict, action_params: dict) -> dict:
    item_name = item.get("name")
    props = item.get("properties", {})
    # project_name = props.get("project_name")
    source_url = props.get("source_url")
    target_url = props.get("target_url")
    app_dir_prop = props.get("app_dir")

    if source_url is None or source_url == "":
        raise ValueError(f"Compose app '{item_name}' does not have a source_url defined for deployment")
    if target_url is None or target_url == "":
        raise ValueError(f"Compose app '{item_name}' does not have a target_url defined for deployment")

    # app_dir = _build_app_dir_path(project_name, item_name)
    app_dir = Path(f"{DATA_DIR}/{app_dir_prop}")
    if not app_dir.exists() or not app_dir.is_dir():
        raise FileNotFoundError(f"Compose app directory '{app_dir}' does not exist")

    # detect compose files in app_dir
    compose_files = []
    knownfiles_list = ["docker-compose.yml", "docker-compose.yaml",
                       "docker-compose.prod.yml", "docker-compose.prod.yaml",
                       "compose.yml", "compose.yaml",
                       "compose.prod.yml", "compose.prod.yaml"]
    for kf in knownfiles_list:
        kf_path = app_dir / kf
        if kf_path.exists() and kf_path.is_file():
            compose_files.append(kf)

    result = deploy_compose_project_to_container_host(host_url=target_url,
                                                      app_name=item_name,
                                                      app_dir=str(app_dir.resolve()),
                                                      compose_args={
                                                          "composefile": compose_files,
                                                          "up_args": ["--build"]
                                                      })
    return result


def _build_app_hash(project_name: str, item_name: str, version: str) -> str:
    import hashlib
    hash_input = f"{project_name}:{item_name}:{version}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def _build_app_key(project_name: str, item_name: str, version: str) -> str:
    def _normalize(s: str) -> str:
        return s.lower().replace(" ", "-").replace("_", "-").replace(".", "-")

    return f"{_normalize(project_name)}-{_normalize(item_name)}-{_normalize(version)}"


def handle_compose_project_configure(item: dict, action_params: dict) -> dict:
    item_name = item.get("name")
    props = item.get("properties", {})

    project_name = props.get("project_name")
    if project_name is None or project_name == "":
        raise ValueError(f"Compose app '{item_name}' does not have a project_name defined in properties")

    app_version = props.get("version", "0.0.0")
    app_hash = _build_app_hash(project_name, item_name, app_version)
    app_key = _build_app_key(project_name, item_name, app_version)

    # app_dir = _build_app_dir_path(project_name, item_name)
    app_dir_prop = props.get("app_dir")
    app_dir = Path(f"{DATA_DIR}/{app_dir_prop}")
    if not app_dir.exists() or not app_dir.is_dir():
        raise FileNotFoundError(f"Compose app directory '{app_dir}' does not exist")

    # we define any overrides to the compose file here
    # e.g. traefik labels, networks, etc.
    compose_env = {}
    compose_env_file = app_dir / ".env"

    # traefik settings
    traefik_enabled = props.get("traefik_enabled", False)
    traefik_network_name = props.get("traefik_network_name")
    traefik_container_port = props.get("traefik_container_port")
    traefik_service_name = props.get("traefik_service_name", "app")
    domain_name = props.get("domain_name")

    # read template.json if exists
    # env_schema = {}
    env_props = {}
    template_file = app_dir / "template.json"
    if template_file.exists():
        with template_file.open("r") as f:
            template_def = json.load(f)
        if isinstance(template_def, dict):
            env_schema = template_def.get("environment", {})
            env_props = env_schema.get("properties", {})

    override_networks = {}
    override_services = {}

    service_labels = [
        "io.mc.app.managed=true",
        f"io.mc.app.name={item_name}",
        f"io.mc.app.project={project_name}",
        f"io.mc.app.version={app_version}",
        f"io.mc.app.hash=sha256:{app_hash}",
        f"io.mc.app.key={app_key}",
    ]
    service_networks = []
    if traefik_enabled:
        if traefik_network_name is None or traefik_network_name == "":
            # raise ValueError(f"Compose app '{item_name}' has traefik_enabled but no traefik_network_name defined")
            traefik_network_name = "traefik-ssl"
        if traefik_container_port is None or traefik_container_port == "":
            raise ValueError(f"Compose app '{item_name}' has traefik_enabled but no traefik_container_port defined")
        if domain_name is None or domain_name == "":
            raise ValueError(f"Compose app '{item_name}' has traefik_enabled but no domain_name defined")

        _traefik_http_enabled = props.get("traefik_http_enabled", False)
        _traefik_https_enabled = props.get("traefik_https_enabled", False)
        _traefik_entrypoint_secure = "websecure"
        _traefik_entrypoint_insecure = "web"

        compose_env.update({
            "TRAEFIK_ENABLED": "true",
            "TRAEFIK_DOMAIN": domain_name,
            "TRAEFIK_NETWORK": traefik_network_name,
            "TRAEFIK_CONTAINER_PORT": str(traefik_container_port),
            "TRAEFIK_ENTRYPOINT": _traefik_entrypoint_secure,
            "TRAEFIK_ENTRYPOINT_INSECURE": _traefik_entrypoint_insecure,
        })

        _service_name = traefik_service_name
        # enable traefik labels for the service
        service_labels += [
            "traefik.enable=true",
            f"traefik.docker.network={traefik_network_name}",
            f"traefik.http.services.{app_key}.loadbalancer.server.port={traefik_container_port}",
        ]
        # connect the service to the traefik network
        service_networks += [traefik_network_name]
        # ensure the traefik network is defined as external
        override_networks[traefik_network_name] = {"external": True}

        if _traefik_http_enabled:
            _router_name = f"{app_key}-http"
            service_labels += [
                f"traefik.http.routers.{_router_name}.rule=Host(`{domain_name}`)",
                f"traefik.http.routers.{_router_name}.entrypoints={_traefik_entrypoint_insecure}",
            ]
        if _traefik_https_enabled:
            _router_name = f"{app_key}-https"
            service_labels += [
                f"traefik.http.routers.{_router_name}.rule=Host(`{domain_name}`)",
                f"traefik.http.routers.{_router_name}.entrypoints={_traefik_entrypoint_secure}",
                f"traefik.http.routers.{_router_name}.tls=true",
                f"traefik.http.routers.{_router_name}.tls.certresolver=le",
            ]

        override_services[_service_name] = {
            "labels": service_labels,
            "networks": service_networks,
        }

    overrides = {
        "services": override_services,
        "networks": override_networks
    }

    # write the overrides to a compose.override.yaml file
    if len(overrides) > 0:
        override_file = app_dir / "compose.override.yaml"
        with override_file.open("w") as f:
            yaml.dump(overrides, f, default_flow_style=False, indent=2)

    # dump the compose_env to the .env file
    if compose_env_file.exists():
        # load existing env file
        existing_env = dotenv.dotenv_values(compose_env_file)
        existing_env.update(compose_env)
        compose_env = existing_env

    # inject env vars from schema
    for k, v in env_props.items():
        default_value = v.get("default", "")
        is_secret = v.get("$secret", False)
        if k not in compose_env:
            if is_secret:
                compose_env[k] = _generate_random_secret()
            elif isinstance(default_value, bool):
                compose_env[k] = "true" if default_value else "false"
            else:
                compose_env[k] = str(default_value)

    compose_env = sorted(compose_env.items())
    for k, v in compose_env:
        dotenv.set_key(compose_env_file, k, v, quote_mode="auto")

    print(f"Configuring compose app '{item_name}' in '{app_dir}'")
    print(compose_env)
    print(overrides)

    return {
        "status": "configured",
        "app_dir": str(app_dir),
        "overrides": overrides,
        # "compose_env": compose_env,
    }


def handle_compose_project_sync(item: dict, action_params: dict) -> dict:
    item_name = item.get("name")
    props = item.get("properties", {})

    project_name = props.get("project_name")
    if project_name is None or project_name == "":
        raise ValueError(f"Compose app '{item_name}' does not have a project_name defined in properties")

    app_dir_prop = props.get("app_dir")
    app_dir = Path(f"{DATA_DIR}/{app_dir_prop}")
    source_url = props.get("source_url")
    if source_url is None or source_url == "":
        raise ValueError(f"Compose app '{item_name}' does not have a source_url defined for sync")

    sschema, surl = source_url.split("://", 1)
    if sschema in ["git", "github"]:

        source_ssh_key_file = None
        source_ssh_key_name = props.get("source_ssh_key_name")
        if source_ssh_key_name is not None and source_ssh_key_name != "":
            source_ssh_key_file = os.path.expanduser(f"~/.ssh/{source_ssh_key_name}")
            if not os.path.exists(source_ssh_key_file):
                raise FileNotFoundError(
                    f"SSH key file '{source_ssh_key_file}' for source_ssh_key_name '{source_ssh_key_name}' not found")

        # return update_project_from_git(source_url, str(app_dir.resolve()), private_key_file=source_ssh_key_file)
        task = update_project_from_git.delay(source_url, str(app_dir.resolve()), private_key_file=source_ssh_key_file)
        return {"status": "syncing", "task_id": task.id}

    elif sschema in ["http", "https"]:
        task = update_project_from_git.delay(source_url, str(app_dir.resolve()))
        return {"status": "syncing", "task_id": task.id}
    else:
        raise ValueError(f"Compose app '{item_name}' has unsupported source_url schema '{sschema}'")


actions = {
    "configure": handle_compose_project_configure,
    "deploy": handle_compose_project_deploy,
    "sync": handle_compose_project_sync,
}

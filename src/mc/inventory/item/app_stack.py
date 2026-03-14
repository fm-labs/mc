import json
import os.path
from dataclasses import dataclass
from pathlib import Path
import shutil
import re
from typing import Literal

import dotenv
import yaml

from mc.config import DATA_DIR
from mc.inventory.storage import get_inventory_storage_instance
from mc.tasks import clone_or_update_git_repo, task_deploy_compose_stack


@dataclass(frozen=True)
class AppStackItem:
    id: str | None = None  # e.g. my-app-project (used as compose project name)
    description: str | None = None
    source_type: Literal["file", "git", "template"] | None = None  # currently only supports source_url as source type
    source_url: str | None = None  # e.g. git://user/repo
    stackfile: str | None = None  # e.g. path/to/docker-compose.yml
    deployment_method: Literal["container", "compose", "swarm", "kubernetes"] | None = None
    deployment_target: str | None = None  # e.g. my-container-host
    domain_name: str | None = None  # optional domain name for the app
    proxy_enabled: bool = False  # whether to auto-wire traefik labels
    proxy_http_enabled: bool = False  # whether to auto-wire traefik labels
    proxy_https_enabled: bool = False  # whether to auto-wire traefik labels
    proxy_service_name: str | None = None  # name of the container service to apply traefik labels to
    proxy_network_name: str | None = None  # name of the docker network traefik is on
    proxy_container_port: int | None = None  # port the app listens on, for traefik routing
    environment: dict | None = None  # environment variables for the app

    def __post_init__(self):
        if self.id is None or self.id == "":
            raise ValueError("AppStackItem 'name' cannot be empty")

    @property
    def slug(self) -> str:
        # normalize app_name
        # normalize with regex to only allow alphanumeric and hyphens
        slug = (self.id.lower().replace(" ", "-").replace("_", "-")
                .replace("/", "-"))
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        return slug

    @property
    def app_dir_path(self) -> Path:
        return _build_app_dir_path(app_name=self.id)

    @property
    def template_config_path(self) -> Path:
        return self.app_dir_path / "template.json"

    def read_template_config(self) -> dict:
        """
        Read and return the template.json configuration for the app stack.
        The template.json file is expected to be in the app directory.
        Raises FileNotFoundError if the template.json file does not exist.
        """
        app_dir = self.app_dir_path
        template_json_file = app_dir / "template.json"
        template_config = None
        if not template_json_file.exists() or not template_json_file.is_file():
            #raise FileNotFoundError(
            #    f"Template JSON file '{template_json_file}' does not exist for stack '{self.id}'")
            return {}
        with template_json_file.open("r") as f:
            template_config = json.load(f)
        return template_config

    def read_stackfile(self) -> str:
        """
        Read and return the stackfile (e.g. docker-compose.yml) content for the app stack.
        The stackfile is expected to be in the app directory.
        Raises FileNotFoundError if the stackfile does not exist.
        """
        app_dir = self.app_dir_path
        stackfile_name = os.path.basename(self.stackfile) or "compose.yaml"
        stackfile_path = app_dir / stackfile_name
        if not stackfile_path.exists() or not stackfile_path.is_file():
            raise FileNotFoundError(
                f"Stackfile '{stackfile_path}' does not exist for container app '{self.id}'")
        with stackfile_path.open("r") as f:
            stackfile_content = f.read()
        return stackfile_content

    # def sync_from_source_url(self):
    #     """
    #     Sync the app stack files from the template repository to the app directory.
    #     Raises FileNotFoundError if the template stackfile does not exist.
    #     """
    #     app_dir = self.app_dir_path
    #     template_dir = _build_template_repo_dir_path(self.source_url)
    #     stackfile = template_dir / (self.stackfile or "compose.yaml")
    #     if not stackfile.exists() or not stackfile.is_file():
    #         raise FileNotFoundError(
    #             f"Template stackfile '{stackfile}' does not exist for container app '{self.id}'")
    #     template_stackdir = stackfile.parent
    #
    #     # copy template stackfile and related files to app_dir,
    #     # overwriting existing files
    #     if not app_dir.exists():
    #         app_dir.mkdir(parents=True, exist_ok=True)
    #     for item in template_stackdir.iterdir():
    #         dest_path = app_dir / item.name
    #         if item.is_dir():
    #             if dest_path.exists():
    #                 shutil.rmtree(dest_path)
    #             shutil.copytree(item, dest_path)
    #         else:
    #             shutil.copy2(item, dest_path)

    @staticmethod
    def from_item_dict(item: dict) -> "AppStackItem":
        #item_name = item.get("name")
        #props = item
        #props["name"] = item_name
        return AppStackItem(**item)


def _build_app_dir_path(app_name: str) -> Path:
    base_dir = Path(f"{DATA_DIR}/apps")
    app_dir = base_dir / app_name
    return app_dir


def _build_template_repo_dir_path(repository_url: str) -> Path:
    repo_key = repository_url.replace("://", "-").replace("/", "-").replace(".", "-")
    base_dir = Path(f"{DATA_DIR}/template_repos")
    repo_dir = base_dir / repo_key
    return repo_dir


def _generate_random_secret(length: int = 32) -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _lookup_container_host_url(host_name: str) -> str:
    storage = get_inventory_storage_instance()
    host_item = storage.get_item_by_name("container_host", host_name)
    if host_item is None:
        raise ValueError(f"Container host '{host_name}' not found in inventory")
    host_props = host_item
    host_url = host_props.get("url")
    if host_url is None or host_url == "":
        raise ValueError(f"Container host '{host_name}' does not have a host_url defined")
    return host_url


def _build_app_hash(owner_id: str, item_name: str, version: str) -> str:
    import hashlib
    hash_input = f"{owner_id}:{item_name}:{version}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def _build_app_key(owner_id: str, item_name: str, version: str) -> str:
    def _normalize(s: str) -> str:
        return (s.lower().replace(" ", "-").replace("_", "-")
                .replace(".", "-").replace("/", "-"))

    return f"{_normalize(owner_id)}-{_normalize(item_name)}"


def _build_appstack_compose_override(app: AppStackItem) -> dict:
    item_name = app.id
    #app_version = app.version or "latest"
    #app_hash = _build_app_hash(project_name, item_name, app_version)
    service_key = _build_app_key("default", item_name, "")

    override_networks = {}
    override_services = {}

    service_networks = []
    service_labels = [
        "mc.app.managed=true",
        f"mc.app.name={item_name}",
        #f"mc.app.version={app_version}",
        # f"mc.app.project={project_name}",
        # f"mc.app.hash=sha256:{app_hash}",
        # f"mc.app.key={app_key}",
    ]

    # traefik settings
    # proxy_enabled = app.proxy_enabled
    # proxy_http_enabled = app.proxy_http_enabled
    # proxy_https_enabled = app.proxy_https_enabled
    proxy_network_name = app.proxy_network_name
    proxy_container_port = app.proxy_container_port
    proxy_service_name = app.proxy_service_name
    domain_name = app.domain_name

    if app.proxy_enabled:
        if proxy_network_name is None or proxy_network_name == "":
            # raise ValueError(f"App stack '{item_name}' has proxy_enabled but no proxy_network_name defined")
            proxy_network_name = "traefik-ssl"

        if proxy_service_name is None or proxy_service_name == "":
            raise ValueError(f"App stack '{item_name}' has proxy_enabled but no proxy_service_name defined")
        if proxy_container_port is None or proxy_container_port == "":
            raise ValueError(f"App stack '{item_name}' has proxy_enabled but no proxy_container_port defined")
        if domain_name is None or domain_name == "":
            raise ValueError(f"App stack '{item_name}' has proxy_enabled but no domain_name defined")

        # connect the service to the traefik network
        service_networks += [proxy_network_name]
        # ensure the traefik network is defined as external
        override_networks[proxy_network_name] = {"external": True}

        # enable traefik labels for the service
        service_labels += [
            "traefik.enable=true",
            f"traefik.docker.network={proxy_network_name}",
            f"traefik.http.services.{service_key}.loadbalancer.server.port={proxy_container_port}",
        ]

        if app.proxy_http_enabled:
            _router_name = f"{service_key}-http"
            service_labels += [
                f"traefik.http.routers.{_router_name}.rule=Host(`{domain_name}`)",
                f"traefik.http.routers.{_router_name}.entrypoints=web",
            ]
        if app.proxy_https_enabled:
            _router_name = f"{service_key}-https"
            service_labels += [
                f"traefik.http.routers.{_router_name}.rule=Host(`{domain_name}`)",
                f"traefik.http.routers.{_router_name}.entrypoints=websecure",
                f"traefik.http.routers.{_router_name}.tls=true",
                f"traefik.http.routers.{_router_name}.tls.certresolver=le",
            ]

        override_services[proxy_service_name] = {
            "labels": service_labels,
            "networks": service_networks,
        }

    overrides = {
        "services": override_services,
        "networks": override_networks
    }
    return overrides


def handle_app_stack_action_prepare(item: dict, action_params: dict) -> dict:
    app = AppStackItem.from_item_dict(item)
    app_dir = app.app_dir_path

    # compose overrides
    # dump the compose overrides to compose.override.yaml
    overrides = _build_appstack_compose_override(app)
    print(overrides)
    if len(overrides) > 0:
        override_file = app_dir / "compose.override.yaml"
        with override_file.open("w") as f:
            yaml.dump(overrides, f, default_flow_style=False, indent=2)
        print(f"Written compose overrides to '{override_file}'")

    # environment variables
    # dump the environment to the .env file, overwriting existing file
    compose_env_file = app_dir / ".env"
    environment = app.environment or {}
    if compose_env_file.exists():
        compose_env_file.unlink()

    for k, v in environment.items():
        dotenv.set_key(compose_env_file, k, str(v), quote_mode="auto")
    print(f"Written environment variables to '{compose_env_file}'")

    return {
        "status": "prepared",
        "app_dir": str(app_dir),
        "overrides": overrides,
        "environment": environment,
    }


def handle_app_stack_action_configure(item: dict, action_params: dict) -> dict:
    """
    Configure the app stack by handling environment variables and other settings.

    :param item: The app stack inventory item.
    :param action_params: Additional parameters for the configure action.
        * environment: A dictionary of environment variables to set for the app stack.
        * merge: Whether to merge the provided environment variables with existing ones (default: False).
    :return: A dictionary indicating the configuration status.
    """
    env_vars = action_params.get("environment", {})
    merge = action_params.get("merge", False)
    if env_vars:
        print("CONFIGUE WITH ENVVARS", env_vars)
        if merge:
            # merge existing environment variables from app properties
            existing_env = item.get("environment", {})
            env_vars = {**existing_env, **env_vars}

        # filter out None and empty string values
        env_vars = {k: v for k, v in env_vars.items() if v is not None and v != ""}
        # update item properties
        #if "properties" not in item:
        #    item["properties"] = {}
        #item["properties"]["environment"] = env_vars
        item["environment"] = env_vars

        storage = get_inventory_storage_instance()
        storage.save_item("app_stack", item)

    return handle_app_stack_action_prepare(item, action_params)


def handle_app_stack_action_sync(item: dict, action_params: dict) -> dict:
    """
    Sync the app stack template repository to the local app directory.
    Raises ValueError if the source_url is not defined or has unsupported schema.

    :param item: The app stack inventory item.
    :param action_params: Additional parameters for the sync action.
        * background: Whether to perform the sync in the background (asynchronous task) or synchronously.
    :return: A dictionary indicating the sync status and task ID.
    """
    app = AppStackItem.from_item_dict(item)
    source_type = app.source_type
    source_url = app.source_url
    if not source_url:
        raise ValueError(f"App stack '{app.id}' does not have a source_url defined for sync")

    background = action_params.get("background", False)

    if source_type == "git":
        sschema, surl = source_url.split("://", 1)
        if sschema in ["git", "github", "http", "https"]:
            # source_ssh_key_file = None
            # source_ssh_key_name = props.get("source_ssh_key_name")
            # if source_ssh_key_name is not None and source_ssh_key_name != "":
            #     source_ssh_key_file = os.path.expanduser(f"~/.ssh/{source_ssh_key_name}")
            #     if not os.path.exists(source_ssh_key_file):
            #         raise FileNotFoundError(
            #             f"SSH key file '{source_ssh_key_file}' for source_ssh_key_name '{source_ssh_key_name}' not found")
            # return update_project_from_git(source_url, str(app_dir.resolve()), private_key_file=source_ssh_key_file)

            template_repo_path = _build_template_repo_dir_path(source_url)
            if background:
                task = clone_or_update_git_repo.delay(source_url, str(template_repo_path.resolve()))
                return {"status": "syncing", "task_id": task.id}
            else:
                return clone_or_update_git_repo(source_url, str(template_repo_path.resolve()))
        else:
            raise ValueError(f"App stack '{app.id}' has unsupported source_url schema '{sschema}'")
    else:
        print(f"App stack '{app.id}' has unsupported source_type '{source_type}' for sync")
        return {"status": "no-op", "message": f"Unsupported source_type '{source_type}' for sync"}


def handle_app_stack_action_deploy(item: dict, action_params: dict) -> dict:
    """
    Deploy the app stack to the specified container host using Docker Compose.
    Raises ValueError if required properties are missing.
    """
    background = action_params.get("background", False)
    handle_app_stack_action_prepare(item, {})  # ensure app is prepared

    app = AppStackItem.from_item_dict(item)
    item_name = app.id
    if not app.deployment_target:
        raise ValueError(f"App stack '{item_name}' does not have a container_host defined for deployment")
    container_host_url = _lookup_container_host_url(app.deployment_target)

    app_dir = app.app_dir_path
    if not app_dir.exists() or not app_dir.is_dir():
        raise FileNotFoundError(f"App stack directory '{app_dir}' does not exist")

    _stackfiles = []
    if app.stackfile:
        _stackfiles.append(os.path.basename(app.stackfile))
        # check if an override file exists
        override_file = app_dir / "compose.override.yaml"
        if override_file.exists() and override_file.is_file():
            _stackfiles.append("compose.override.yaml")

    if background:
        task = task_deploy_compose_stack.delay(project_name=app.id,
                                               project_dir=str(app_dir.resolve()),
                                               stackfile=_stackfiles,
                                               host_url=container_host_url)
        return {"status": "deploying", "task_id": task.id}

    return task_deploy_compose_stack(project_name=app.id,
                                     project_dir=str(app_dir.resolve()),
                                     stackfile=_stackfiles,
                                     host_url=container_host_url)


def handle_app_stack_view_template_config(item: dict, view_params: dict) -> dict:
    """
    Return the content of the template.json configuration for the app stack.
    """
    app = AppStackItem.from_item_dict(item)
    return app.read_template_config()


def handle_app_stack_view_stackfile(item: dict, view_params: dict) -> dict:
    """
    Return the content of the stackfile (e.g. docker-compose.yml) for the app stack.
    """
    app = AppStackItem.from_item_dict(item)
    content = app.read_stackfile()
    return {"content": content}


actions = {
    "configure": handle_app_stack_action_configure,
    "deploy": handle_app_stack_action_deploy,
    "sync": handle_app_stack_action_sync,
}

views = {
    "template": handle_app_stack_view_template_config,
    "stackfile": handle_app_stack_view_stackfile,
}

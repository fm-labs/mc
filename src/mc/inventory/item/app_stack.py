import json
import os.path
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import logging

import dotenv
import yaml

from mc import logs
from mc.config import DATA_DIR
from mc.inventory.storage import get_inventory_storage_instance
from mc.tasks import clone_or_update_git_repo, task_deploy_compose_project, task_destroy_compose_project

logger = logging.getLogger(__name__)
logger.addHandler(logs.get_rotating_file_log_handler("app_stack"))


@dataclass(frozen=True)
class AppStackItem:
    id: str | None = None  # e.g. my-app-project (used as compose project name)
    type: Literal["container", "compose", "swarm", "kubernetes"] | None = None
    label: str | None = None
    description: str | None = None
    repository: dict | None = None  # e.g. {"type": "git", "url": "git://user/repo", "branch": "main", "template_path": "path/to/stack/files"}
    stackfile: str | None = None  # e.g. compose.yaml
    target_node: str | None = None
    domain_name: str | None = None  # optional domain name for the app
    proxy_enabled: bool = False  # whether to auto-wire traefik labels
    proxy_http_enabled: bool = False  # enable http routing
    proxy_https_enabled: bool = False  # enable https routing
    proxy_https_redirect: bool = False  # auto-redirect http to https
    proxy_service_name: str | None = None  # name of the container service to route to
    proxy_container_port: int | None = None  # port of the container service to route to
    proxy_network_name: str | None = None  # name of the docker network traefik is on
    environment: dict | None = None  # environment variables for the app
    item_type: str = "app_stack"  # todo remove

    def __post_init__(self):
        if self.id is None or self.id == "":
            raise ValueError("AppStackItem 'name' cannot be empty")

    # @property
    # def slug(self) -> str:
    #    # normalize app_name
    #    # normalize with regex to only allow alphanumeric and hyphens
    #    slug = (self.id.lower().replace(" ", "-").replace("_", "-")
    #            .replace("/", "-"))
    #    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    #    return slug

    @property
    def app_dir_path(self) -> Path:
        return _build_app_dir_path(app_name=self.id)

    # @property
    # def template_config_path(self) -> Path:
    #    return self.app_dir_path / "template.json"

    def read_stackconf(self) -> dict:
        """
        Read and return the template.json configuration for the app stack.
        The template.json file is expected to be in the app directory.
        Raises FileNotFoundError if the template.json file does not exist.
        """
        app_dir = self.app_dir_path
        template_json_file = app_dir / "template.json"
        template_config = None
        if not template_json_file.exists() or not template_json_file.is_file():
            raise FileNotFoundError(
                f"Template JSON file '{template_json_file}' does not exist for stack '{self.id}'")
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
        stackfile_name = self.stackfile or "compose.yaml"
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
        # item_name = item.get("name")
        # props = item
        # props["name"] = item_name
        # rint("FROM ITEM DICT", item)
        return AppStackItem(**item)


def _build_app_dir_path(app_name: str) -> Path:
    base_dir = Path(f"{DATA_DIR}/apps")
    app_dir = base_dir / app_name
    return app_dir


def _build_repo_cache_path(repository_url: str) -> Path:
    repo_key = repository_url.replace("://", "-").replace("/", "-").replace(".", "-")
    base_dir = Path(f"{DATA_DIR}/cache/repos")
    repo_dir = base_dir / repo_key
    return repo_dir


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
    # app_version = app.version or "latest"
    # app_hash = _build_app_hash(project_name, item_name, app_version)
    service_key = _build_app_key("default", item_name, "")

    override_networks = {}
    override_services = {}

    service_networks = []
    service_labels = [
        "mc.app.managed=true",
        f"mc.app.name={item_name}",
        # f"mc.app.version={app_version}",
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


def handle_app_stack_action_sync(item: dict, action_params: dict) -> dict:
    """
    Sync the app stack template repository to the local app directory.
    Raises ValueError if the source_url is not defined or has unsupported schema.

    :param item: The app stack inventory item.
    :param action_params: Additional parameters for the sync action.
        * background: Whether to perform the sync in the background (asynchronous task) or synchronously.
    :return: A dictionary indicating the sync status and task ID.
    """
    logger.info(f"Syncing app stack '{item.get('id')}' with action_params: {action_params}")
    background = action_params.get("background", False)

    app = AppStackItem.from_item_dict(item)
    if app.repository:
        repo_url = app.repository.get("url", "")
        repo_path = app.repository.get("path", "")
        if not repo_url:
            raise ValueError(f"App stack '{app.id}' has repository defined but no URL for sync")

        sschema, surl = repo_url.split("://", 1)
        if sschema in ["http", "https"]:
            # source_ssh_key_file = None
            # source_ssh_key_name = props.get("source_ssh_key_name")
            # if source_ssh_key_name is not None and source_ssh_key_name != "":
            #     source_ssh_key_file = os.path.expanduser(f"~/.ssh/{source_ssh_key_name}")
            #     if not os.path.exists(source_ssh_key_file):
            #         raise FileNotFoundError(
            #             f"SSH key file '{source_ssh_key_file}' for source_ssh_key_name '{source_ssh_key_name}' not found")
            # return update_project_from_git(source_url, str(app_dir.resolve()), private_key_file=source_ssh_key_file)

            checkout_path = _build_repo_cache_path(repo_url)
            checkout_path.parent.mkdir(parents=True, exist_ok=True)

            is_private = app.repository.get("private", False)
            if is_private and "@" not in repo_url:
                repo_auth_username = app.repository.get("auth", {}).get("username", "")
                repo_auth_password = app.repository.get("auth", {}).get("password", "")
                repo_url = repo_url.replace("://", f"://{repo_auth_username}:{repo_auth_password}@", 1)

            # if background:
            #    task = clone_or_update_git_repo.delay(repo_url, str(checkout_path.resolve()))
            #    return {"status": "syncing", "task_id": task.id}
            # else:

            logger.info(f"Syncing repository '{repo_url}' to cache path '{checkout_path}' for app stack '{app.id}'")
            _repo_url = os.path.expandvars(repo_url)
            # todo add support for ssh key auth by looking up the key file path from the inventory based on a reference in the repository config
            logger.debug(f"Expanded repository URL: '{_repo_url}'")
            # print(f"Syncing repository '{repo_url}' to cache path '{checkout_path}' for app stack '{app.id}'")

            clone_result = clone_or_update_git_repo(_repo_url, str(checkout_path.resolve()))
            if clone_result.get("return_code") != 0:
                raise ValueError(f"Error syncing repository: {clone_result.get('stderr')}")

            # after syncing the template repo, copy the stackfile and related files to the app dir
            import shutil
            target_dir = app.app_dir_path
            template_dir = checkout_path / repo_path
            if not template_dir.exists() or not template_dir.is_dir():
                raise FileNotFoundError(
                    f"Template directory '{template_dir}' does not exist in repository for app stack '{app.id}'")

            # wipe the target dir if it exists
            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.copytree(str(template_dir), str(target_dir))

            # handle_app_stack_action_configure(item, {})
            return {"status": "synced", "app_dir": str(target_dir), "repo_url": repo_url, "repo_path": repo_path}

        else:
            raise ValueError(f"App stack '{app.id}' has unsupported source_url schema '{sschema}'")
    else:
        logger.warning(f"App stack '{app.id}' has no repository to sync")
        return {"status": "no-op", "message": f"No repository to sync"}


def handle_app_stack_action_configure(item: dict, action_params: dict) -> dict:
    """
    Configure the app stack by handling environment variables and other settings.

    :param item: The app stack inventory item.
    :param action_params: Additional parameters for the configure action.
        * environment: A dictionary of environment variables to set for the app stack.
        * merge: Whether to merge the provided environment variables with existing ones (default: False).
    :return: A dictionary indicating the configuration status.
    """
    logger.info(f"Configuring app stack '{item.get('id')}' with action_params: {action_params}")
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
        # if "properties" not in item:
        #    item["properties"] = {}
        # item["properties"]["environment"] = env_vars
        item["environment"] = env_vars

        storage = get_inventory_storage_instance()
        storage.save_item("app_stack", item)

    return handle_app_stack_action_prepare(item, action_params)


def handle_app_stack_action_prepare(item: dict, action_params: dict) -> dict:
    logger.info(f"Preparing app stack '{item.get('id')}' with action_params: {action_params}")
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
        logger.info(f"Written compose overrides to '{override_file}'")

    # environment variables
    # dump the environment to the .env file, overwriting existing file
    compose_env_file = app_dir / ".env"
    environment = app.environment or {}
    if compose_env_file.exists():
        compose_env_file.unlink()

    for k, v in environment.items():
        dotenv.set_key(compose_env_file, k, str(v), quote_mode="auto")
    logger.info(f"Written environment variables to '{compose_env_file}'")

    return {
        "status": "prepared",
        "app_dir": str(app_dir),
        "overrides": overrides,
        "environment": environment,
    }


def handle_app_stack_action_deploy(item: dict, action_params: dict) -> dict:
    """
    Deploy the app stack to the specified container host using Docker Compose.
    Raises ValueError if required properties are missing.
    """
    logger.info(f"Deploying app stack '{item.get('id')}' with action_params: {action_params}")
    confirm = action_params.get("confirm", False)
    background = action_params.get("background", False)
    up_args = {
        "build": action_params.get("build", False),
        "remove_orphans": action_params.get("remove_orphans", False),
        # "timeout": action_params.get("timeout", 120),
    }

    if not confirm:
        raise ValueError("Please confirm")

    # ensure app is prepared
    handle_app_stack_action_prepare(item, {})

    # validate app directory and stackfile
    app = AppStackItem.from_item_dict(item)
    app_dir = app.app_dir_path
    if not app_dir.exists() or not app_dir.is_dir():
        raise FileNotFoundError(f"App stack directory '{app_dir}' does not exist")

    project_dir = app_dir
    project_stackfiles = []
    if app.stackfile:
        stackfile_name = app.stackfile
        project_stackfiles.append(stackfile_name)
        # check if an override file exists
        override_file = project_dir / stackfile_name.replace(".yaml", ".override.yaml").replace(".yml",
                                                                                                ".override.yaml")
        if override_file.exists() and override_file.is_file():
            project_stackfiles.append("compose.override.yaml")
        # check if a mc override file exists
        override_file = project_dir / "mc.override.yaml"
        if override_file.exists() and override_file.is_file():
            project_stackfiles.append("mc.override.yaml")

    # target_node = app.target_node or "localdocker"
    # if not app.target_node:
    #    raise ValueError(f"App stack '{item_name}' does not have a container_host defined for deployment")
    # container_host_url = _lookup_container_host_url(target_node)
    container_host_url = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")

    # if background:
    #     task = task_deploy_compose_project.delay(project_name=app.id,
    #                                              project_dir=str(project_dir.resolve()),
    #                                              stackfile=project_stackfiles,
    #                                              host_url=container_host_url)
    #     return {"status": "deploying", "task_id": task.id}

    return task_deploy_compose_project(project_name=app.id,
                                       project_dir=str(project_dir.resolve()),
                                       stackfile=project_stackfiles,
                                       host_url=container_host_url,
                                       **up_args)


def handle_app_stack_redeploy(item: dict, action_params: dict) -> dict:
    """
    Redeploy the app stack by performing a down followed by an up deployment.
    Raises ValueError if required properties are missing.
    """
    logger.info(f"Redeploying app stack '{item.get('id')}' with action_params: {action_params}")
    confirm = action_params.get("confirm", False)
    background = False  # action_params.get("background", False)
    sync = action_params.get("sync", False)
    build = action_params.get("build", False)
    remove_orphans = action_params.get("remove_orphans", False)

    if not confirm:
        raise ValueError("Please confirm")

    if sync:
        handle_app_stack_action_sync(item, {"confirm": True})

    handle_app_stack_action_configure(item, {"confirm": True, "background": background})
    # handle_app_stack_action_prepare(item, {"confirm": confirm}) # prepare is called inside configure
    return handle_app_stack_action_deploy(item, {"confirm": True, "background": background,
                                                 "build": build, "remove_orphans": remove_orphans})


def handle_app_stack_action_destroy(item: dict, action_params: dict) -> dict:
    """Destroy the app stack by removing the deployed containers and related resources from the target container host."""
    confirm = action_params.get("confirm", False)
    background = action_params.get("background", False)
    destroy_args = {
        "timeout": action_params.get("timeout", 30),
    }

    if not confirm:
        raise ValueError("Please confirm")

    app = AppStackItem.from_item_dict(item)
    app_dir = app.app_dir_path
    if not app_dir.exists() or not app_dir.is_dir():
        raise FileNotFoundError(f"App stack directory '{app_dir}' does not exist")
    project_dir = app_dir
    container_host_url = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")

    return task_destroy_compose_project(project_name=app.id,
                                        project_dir=str(project_dir.resolve()),
                                        stackfile=[],
                                        host_url=container_host_url,
                                        **destroy_args)


def handle_app_stack_view_template_config(item: dict, view_params: dict) -> dict:
    """
    Return the content of the template.json configuration for the app stack.
    """
    app = AppStackItem.from_item_dict(item)
    return app.read_stackconf()


def handle_app_stack_view_stackfile(item: dict, view_params: dict) -> dict:
    """
    Return the content of the stackfile (e.g. docker-compose.yml) for the app stack.
    """
    app = AppStackItem.from_item_dict(item)
    content = app.read_stackfile()
    return {"content": content}


actions = {
    "sync": handle_app_stack_action_sync,
    "configure": handle_app_stack_action_configure,
    "deploy": handle_app_stack_action_deploy,
    "redeploy": handle_app_stack_redeploy,
    "destroy": handle_app_stack_action_destroy,
}

views = {
    "template": handle_app_stack_view_template_config,
    "stackfile": handle_app_stack_view_stackfile,
}

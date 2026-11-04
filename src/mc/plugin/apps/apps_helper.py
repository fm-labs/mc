import os
from typing import Literal, Any

import pydantic
import yaml

from mc.config import MC_HOME, get_mc_real_path
from mc.docker.compose_runner import LocalDockerComposeStackRunner, DockerComposeUpArgs
from mc.util.yaml_util import yaml_dump


def get_app_dir(app_name: str) -> str:
    return os.path.join(MC_HOME, "apps", app_name)

class AppVolumeSpec(pydantic.BaseModel):
    volume_name: str
    container_path: str
    bind: bool = False
    host_path: str | None = None # only if bind == True

class AppNetworkSpec(pydantic.BaseModel):
    network_name: str
    external: bool = False

class AppSpec(pydantic.BaseModel):
    id: str
    type: Literal["container", "compose"]
    title: str | None = None
    description: str | None = None
    image: str | None = None # only container
    stackfile: str | None = None # only compose
    volumes: list[AppVolumeSpec] | None = pydantic.Field(default_factory=list) # overrides
    networks: list[AppNetworkSpec] | None = pydantic.Field(default_factory=list) # overrides
    environment: dict[str, str] | None = pydantic.Field(default_factory=dict) # overrides


    @property
    def project_dir(self) -> str:
        return get_app_dir(self.id)

    @property
    def real_project_dir(self) -> str:
        return str(get_mc_real_path(self.project_dir))

    def read_stackfile(self) -> str:
        if self.stackfile is None:
            raise RuntimeError("No stackfile specified")
        with open(os.path.join(get_app_dir(self.id), self.stackfile), "r") as f:
            return f.read()

    @staticmethod
    def parse_stackfile(contents: str) -> dict[str, Any]:
        return yaml.safe_load(contents)

    def compile(self, vars: dict[str, str]) -> None:
        """Compile compose.yaml, compose.override.yaml, compose.traefik.yaml, etc."""

        stack = self.parse_stackfile(self.read_stackfile())

        # compose.override.yaml
        target_path = os.path.join(get_app_dir(self.id), "compose.override.yaml")
        services = {}
        networks = {}
        volumes = {}
        override = {"services": services, "networks": networks, "volumes": volumes}
        yaml_dump(override, target_path)

        # compose.traefik.yaml
        target_path = os.path.join(get_app_dir(self.id), "compose.traefik.yaml")
        services = {}
        networks = {}
        override = {"services": services, "networks": networks, "volumes": volumes}
        yaml_dump(override, target_path)


    def run(self) -> None:
        if self.type == "compose":
            if not self.stackfile:
                raise RuntimeError("Compose project must have a stackfile")

            stackfiles = [
                os.path.join(get_app_dir(self.id), self.stackfile),
                os.path.join(get_app_dir(self.id), "compose.override.yaml"),
                os.path.join(get_app_dir(self.id), "compose.traefik.yaml"),
            ]

            runner = LocalDockerComposeStackRunner(
                self.id,
                self.real_project_dir,
                stackfiles=stackfiles,
            )
            runner.up(DockerComposeUpArgs(
                remove_orphans=True,
                quiet_pull=True,
                yes=True,
                no_color=True,
            ))
        else:
            raise NotImplementedError()


    @staticmethod
    def create_from_string(name: str, contents: str) -> "AppSpec":
        # dump contents to project dir
        with open(os.path.join(get_app_dir(name), "compose.yaml"), "w") as f:
            f.write(contents)
        return AppSpec(id=name, type="compose", stackfile="compose.yaml")
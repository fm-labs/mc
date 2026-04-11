from __future__ import annotations

from dataclasses import dataclass, field
import yaml


@dataclass
class Build:
    context: str
    dockerfile: str | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict | str:
        if self.dockerfile is None and not self.extra:
            return self.context
        result = {"context": self.context}
        if self.dockerfile is not None:
            result["dockerfile"] = self.dockerfile
        result.update(self.extra)
        return result


@dataclass
class Service:
    name: str
    image: str | None = None
    build: Build | str | None = None
    labels: dict[str, str] | list[str] | None = None
    command: str | list[str] | None = None
    networks: list[str] | dict | None = None
    volumes: list[str] | None = None
    ports: list[str] | None = None
    expose: list[str | int] | None = None
    environment: dict[str, str] | list[str] | None = None
    restart: str | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {}
        if self.image is not None:
            result["image"] = self.image
        if self.build is not None:
            result["build"] = self.build.to_dict() if isinstance(self.build, Build) else self.build
        if self.labels is not None:
            result["labels"] = self.labels
        if self.command is not None:
            result["command"] = self.command
        if self.networks is not None:
            result["networks"] = self.networks
        if self.volumes is not None:
            result["volumes"] = self.volumes
        if self.ports is not None:
            result["ports"] = self.ports
        if self.expose is not None:
            result["expose"] = self.expose
        if self.environment is not None:
            result["environment"] = self.environment
        if self.restart is not None:
            result["restart"] = self.restart
        result.update(self.extra)
        return result

    def to_docker_cmd(self, detach: bool = True, pretty_print=False) -> str:
        parts = ["docker", "container", "run"]
        if detach:
            parts.append("-d")
        parts.append(f"--name {self.name}")
        if self.restart:
            parts.append(f"--restart {self.restart}")
        for p in self.ports or []:
            parts.append(f"-p {p}")
        for e in self.expose or []:
            parts.append(f"--expose {e}")
        for v in self.volumes or []:
            parts.append(f"-v {v}")
        for n in (self.networks if isinstance(self.networks, list) else []):
            parts.append(f"--network {n}")
        if isinstance(self.labels, list):
            for label in self.labels:
                parts.append(f'-l "{label}"')
        elif isinstance(self.labels, dict):
            for k, v in self.labels.items():
                parts.append(f'-l "{k}={v}"')
        if isinstance(self.environment, dict):
            for k, v in self.environment.items():
                parts.append(f"-e {k}={v}")
        elif isinstance(self.environment, list):
            for e in self.environment:
                parts.append(f"-e {e}")
        parts.append(self.image)
        if isinstance(self.command, list):
            parts.extend(self.command)
        elif isinstance(self.command, str):
            parts.append(self.command)

        if pretty_print:
            return " \\\n  ".join(parts)
        return " ".join(parts)


@dataclass
class Compose:
    services: list[Service] = field(default_factory=list)
    version: str | None = None
    networks: dict | None = None
    volumes: dict | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {}
        if self.version is not None:
            result["version"] = self.version
        result["services"] = {svc.name: svc.to_dict() for svc in self.services}
        if self.networks is not None:
            result["networks"] = self.networks
        if self.volumes is not None:
            result["volumes"] = self.volumes
        result.update(self.extra)
        return result

    def to_compose_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

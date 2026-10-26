"""
Container client for another mc instance ("node"), using its /api/containers routes.

The client mimics the parts of the docker SDK client that the container routes use (containers, images, volumes,
networks, info, version, df, events), so a node can be registered in the ContainerClientsManager like a local
docker or podman connection.

Nodes are configured in the "nodes" section of the mc config file:

    "nodes": {
        "srv03": {
            "base_url": "http://srv03:3080",
            "api_key": "...",
            "remote_alias": "localdocker",   # optional, container connection on the node
            "autoconnect": true              # optional
        }
    }
"""

from __future__ import annotations

import json
import logging
import shlex
from collections.abc import Iterator
from typing import Any, NamedTuple

import requests
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
CONNECT_TIMEOUT = 5.0


class NodeConfig(BaseModel):
    name: str
    base_url: str
    api_key: str | None = None
    remote_alias: str = "localdocker"
    autoconnect: bool = True
    timeout: float = DEFAULT_TIMEOUT


def load_node_configs(config: dict[str, Any]) -> list[NodeConfig]:
    """Read the node configs from the "nodes" section of the mc config. Invalid entries are logged and skipped."""
    nodes = config.get("nodes") or {}
    if not isinstance(nodes, dict):
        logger.error("Invalid 'nodes' section in mc config: expected an object")
        return []

    result: list[NodeConfig] = []
    for name, entry in nodes.items():
        if not isinstance(entry, dict):
            logger.error("Invalid node config '%s': expected an object", name)
            continue
        try:
            result.append(NodeConfig.model_validate({**entry, "name": name}))
        except ValidationError as e:
            logger.error("Invalid node config '%s': %s", name, e)
    return result


class NodeApiError(HTTPException):
    """A failed request to a node. It's an HTTPException, so routes return the node's status (or 502)."""


class ExecResult(NamedTuple):
    exit_code: int | None
    output: bytes


class RemoteObject:
    """A docker SDK-like model: an object with attrs, backed by a node."""

    path = ""

    def __init__(self, client: NodeContainerClient, attrs: dict[str, Any]) -> None:
        self.client = client
        self.attrs = attrs

    @property
    def id(self) -> str | None:
        return self.attrs.get("Id") or self.attrs.get("Name")

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.id}>"


class RemoteContainer(RemoteObject):
    @property
    def name(self) -> str:
        return (self.attrs.get("Name") or "").lstrip("/")

    def _path(self, suffix: str = "") -> str:
        return f"containers/{self.id}{suffix}"

    def _action(self, action: str) -> None:
        self.client._json("POST", self._path(f"/actions/{action}"))

    def start(self, **_: Any) -> None:
        self._action("start")

    def stop(self, **_: Any) -> None:
        self._action("stop")

    def restart(self, **_: Any) -> None:
        self._action("restart")

    def pause(self) -> None:
        self._action("pause")

    def unpause(self) -> None:
        self._action("unpause")

    def remove(self, **_: Any) -> None:
        # the node always removes with force=True
        self._action("remove")

    def reload(self) -> None:
        self.attrs = self.client._json("GET", self._path())

    def exec_run(self, cmd: str | list[str], **_: Any) -> ExecResult:
        command = cmd if isinstance(cmd, str) else shlex.join(cmd)
        result = self.client._json("POST", self._path("/exec"), json={"command": command})
        return ExecResult(result.get("exit_code"), (result.get("output") or "").encode("utf-8"))

    def logs(
        self,
        stream: bool = False,
        follow: bool = False,
        since: int | None = None,
        until: int | None = None,
        tail: int | str | None = None,
        **_: Any,
    ) -> bytes | Iterator[bytes]:
        params: dict[str, Any] = {k: v for k, v in {"since": since, "until": until, "tail": tail}.items() if v}
        if not stream:
            result = self.client._json("GET", self._path("/logs"), params=params)
            return "\n".join(result.get("logs") or []).encode("utf-8")

        params.update({"follow": str(follow).lower(), "format": "json"})
        response = self.client._request("GET", self._path("/logs/stream"), params=params, stream=True)
        return _iter_ndjson(response, lambda line: line.get("log", "").encode("utf-8"))


class RemoteImage(RemoteObject):
    @property
    def tags(self) -> list[str]:
        return self.attrs.get("RepoTags") or []


class RemoteVolume(RemoteObject):
    pass


class RemoteNetwork(RemoteObject):
    pass


class RemoteCollection:
    """A docker SDK-like collection (client.containers, client.images, ...)."""

    path = ""
    model: type[RemoteObject] = RemoteObject

    def __init__(self, client: NodeContainerClient) -> None:
        self.client = client

    def list(self, *_: Any, **__: Any) -> list[Any]:
        # the node applies its own filters (e.g. all=True for containers)
        return [self.model(self.client, attrs) for attrs in self.client._json("GET", self.path)]

    def get(self, object_id: str) -> Any:
        return self.model(self.client, self.client._json("GET", f"{self.path}/{object_id}"))


class RemoteContainers(RemoteCollection):
    path = "containers"
    model = RemoteContainer


class RemoteImages(RemoteCollection):
    path = "images"
    model = RemoteImage

    def pull(self, repository: str, tag: str | None = None, **_: Any) -> RemoteImage:
        image = f"{repository}:{tag}" if tag else repository
        return RemoteImage(self.client, self.client._json("POST", f"{self.path}/pull", json={"image": image}))


class RemoteVolumes(RemoteCollection):
    path = "volumes"
    model = RemoteVolume


class RemoteNetworks(RemoteCollection):
    path = "networks"
    model = RemoteNetwork

    def get(self, object_id: str) -> Any:
        # the node has no route for a single network
        for network in self.list():
            if object_id in (network.attrs.get("Id"), network.attrs.get("Name")):
                return network
        raise NodeApiError(404, f"Network '{object_id}' not found on node")


def _iter_ndjson(response: requests.Response, convert) -> Iterator[Any]:
    """Yield the converted lines of an NDJSON response. Closing the iterator closes the response."""
    try:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                yield convert(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping invalid line from node stream: %r", line[:200])
    finally:
        response.close()


class NodeContainerClient:
    """Container client for a container connection ("remote_alias") on another mc instance."""

    engine = "node"

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        remote_alias: str = "localdocker",
        timeout: float = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.remote_alias = remote_alias
        self.timeout = timeout
        self.session = session or requests.Session()
        if api_key:
            self.session.headers["x-api-key"] = api_key

    @classmethod
    def from_config(cls, node: NodeConfig) -> NodeContainerClient:
        return cls(base_url=node.base_url, api_key=node.api_key, remote_alias=node.remote_alias, timeout=node.timeout)

    def __repr__(self) -> str:
        return f"<NodeContainerClient {self.base_url} alias={self.remote_alias}>"

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/containers/{self.remote_alias}/{path.lstrip('/')}"

    def _request(
        self, method: str, path: str, *, url: str | None = None, stream: bool = False, **kwargs: Any
    ) -> requests.Response:
        url = url or self._url(path)
        logger.info(f"Sending request to {url}")
        # streams can stay open for a long time, so only the connection has a timeout
        kwargs.setdefault("timeout", (CONNECT_TIMEOUT, None) if stream else self.timeout)
        try:
            response = self.session.request(method, url, stream=stream, **kwargs)
        except requests.RequestException as e:
            raise NodeApiError(502, f"Node {self.base_url} is unreachable: {e}") from e

        if response.status_code >= 400:
            detail = _error_detail(response)
            response.close()
            raise NodeApiError(response.status_code, f"Node {self.base_url}: {detail}")
        return response

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as e:
            raise NodeApiError(502, f"Node {self.base_url} returned invalid JSON") from e

    def ping(self) -> bool:
        self._request("GET", "", url=f"{self.base_url}/api/health")
        return True

    def version(self) -> dict[str, Any]:
        return self._json("GET", "version")

    def info(self) -> dict[str, Any]:
        return self._json("GET", "info")

    def df(self) -> dict[str, Any]:
        return self._json("GET", "df")

    def events(self, decode: bool = True, **_: Any) -> Iterator[Any]:
        response = self._request("GET", "events/stream", stream=True)
        if decode:
            return _iter_ndjson(response, lambda event: event)
        return _iter_ndjson(response, lambda event: json.dumps(event).encode("utf-8"))

    @property
    def containers(self) -> RemoteContainers:
        return RemoteContainers(self)

    @property
    def images(self) -> RemoteImages:
        return RemoteImages(self)

    @property
    def volumes(self) -> RemoteVolumes:
        return RemoteVolumes(self)

    @property
    def networks(self) -> RemoteNetworks:
        return RemoteNetworks(self)

    def close(self) -> None:
        self.session.close()


def _error_detail(response: requests.Response) -> str:
    """The error message from a Problem JSON or FastAPI error response."""
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("error") or body)
    return str(body)

"""
NodeContainerClient against a "remote" mc app: the container routes, served by a TestClient and backed by a fake
docker client. Requests from the node client are sent to the remote app through a requests adapter.
"""

import io
from typing import Any

import pytest
import requests
from fastapi import FastAPI, Security
from fastapi.testclient import TestClient
from requests.adapters import BaseAdapter
from requests.structures import CaseInsensitiveDict

from mc.plugin.containers.manager import ContainerClientsManager, bootstrap_container_connection_manager
from mc.plugin.containers.node_client import NodeApiError, NodeConfig, NodeContainerClient, parse_node_configs
from mc.server import deps

API_KEY = "node-test-api-key"
NODE_URL = "http://node1:3080"


class FakeModel:
    def __init__(self, attrs: dict[str, Any]) -> None:
        self.attrs = attrs
        self.id = attrs["Id"]


class FakeContainer(FakeModel):
    def __init__(self, attrs: dict[str, Any]) -> None:
        super().__init__(attrs)
        self.calls: list[str] = []

    def start(self):
        self.calls.append("start")
        self.attrs["State"]["Running"] = True

    def stop(self):
        self.calls.append("stop")
        self.attrs["State"]["Running"] = False

    def reload(self):
        pass

    def exec_run(self, cmd, **_):
        return type("ExecResult", (), {"exit_code": 0, "output": f"ran {cmd}".encode()})()

    def top(self, ps_args=None, **_):
        self.calls.append(f"top {ps_args}")
        return {"Titles": ["PID", "CMD"], "Processes": [["1", "nginx"]]}

    def logs(self, stream=False, **_):
        lines = [b"line one\n", b"line two\n"]
        return iter(lines) if stream else b"".join(lines)


class FakeCollection:
    def __init__(self, items: list[FakeModel]) -> None:
        self.items = {i.id: i for i in items}

    def list(self, *_, **__):
        return list(self.items.values())

    def get(self, object_id):
        if object_id not in self.items:
            from docker.errors import NotFound

            raise NotFound(f"{object_id} not found")
        return self.items[object_id]


class FakeDocker:
    def __init__(self) -> None:
        self.container = FakeContainer({"Id": "c1", "Name": "/web", "State": {"Running": False}})
        self.containers = FakeCollection([self.container])
        self.images = FakeCollection([FakeModel({"Id": "sha256:img1", "RepoTags": ["nginx:latest"]})])
        self.volumes = FakeCollection([FakeModel({"Id": "vol1", "Name": "vol1"})])
        self.networks = FakeCollection([FakeModel({"Id": "net1", "Name": "bridge"})])

    def version(self):
        return {"Version": "27.0.0"}

    def info(self):
        return {"Name": "remote-host"}

    def df(self):
        return {"LayersSize": 1}

    def events(self, decode=True):
        return iter([{"Type": "container", "Action": "start"}])

    def ping(self):
        return True

    def close(self):
        pass


class AppAdapter(BaseAdapter):
    """Sends requests made with `requests` to a TestClient."""

    def __init__(self, client: TestClient) -> None:
        super().__init__()
        self.client = client

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        r = self.client.request(request.method, request.url, headers=dict(request.headers), content=request.body)
        response = requests.Response()
        response.status_code = r.status_code
        response.headers = CaseInsensitiveDict(r.headers)
        response.raw = io.BytesIO(r.content)
        response.url = request.url
        response.request = request
        response.encoding = "utf-8"
        return response

    def close(self):
        pass


@pytest.fixture
def remote_docker() -> FakeDocker:
    return FakeDocker()


@pytest.fixture
def remote_app(remote_docker, monkeypatch) -> TestClient:
    """The remote mc instance: the container routes with API key auth and a fake 'localhost' connection."""
    from mc.cache import cache_store
    from mc.plugin.containers.routes import router

    monkeypatch.setattr(deps, "MC_API_KEY", API_KEY)
    # the routes cache their results, don't serve results of other tests
    monkeypatch.setattr(cache_store, "read_cache", lambda key: None)

    app = FastAPI()
    app.state.ccm = ContainerClientsManager()
    app.state.ccm.register("localhost", remote_docker, "docker+fake")
    app.include_router(router, prefix="/api", dependencies=[Security(deps.dep_auth_user)])

    @app.get("/api/health")
    def health():
        return {"status": "OK"}

    return TestClient(app)


def make_node_client(remote_app: TestClient, api_key: str | None = API_KEY) -> NodeContainerClient:
    session = requests.Session()
    session.mount(NODE_URL, AppAdapter(remote_app))
    return NodeContainerClient(base_url=NODE_URL, api_key=api_key, session=session)


@pytest.fixture
def node(remote_app) -> NodeContainerClient:
    return make_node_client(remote_app)


def test_parse_node_configs_skips_invalid_entries():
    nodes = parse_node_configs(
        {
            "docker_hosts": {
                "srv03": {"url": "node+http://srv03:3080", "api_key": "k1"},
                "local": {"url": "unix:///var/run/docker.sock"},
                "broken": {"api_key": "no-url"},
                "wrong": "not-an-object",
            }
        }
    )
    assert [n.name for n in nodes] == ["srv03"]
    assert nodes[0].api_key == "k1"
    assert nodes[0].remote_alias == "localhost"
    assert NodeContainerClient.from_config(nodes[0]).base_url == "http://srv03:3080"


def test_parse_node_configs_without_nodes():
    assert parse_node_configs({}) == []


def test_ping_and_system_info(node):
    assert node.ping() is True
    assert node.version() == {"Version": "27.0.0"}
    assert node.info() == {"Name": "remote-host"}
    assert node.df() == {"LayersSize": 1}


def test_sends_api_key(remote_app):
    with pytest.raises(NodeApiError) as e:
        make_node_client(remote_app, api_key="wrong-api-key").version()
    # 401 from the node is returned as 400, so the local UI doesn't log out
    assert e.value.status_code == 400
    assert "(401)" in e.value.detail


def test_list_and_get(node):
    containers = node.containers.list(all=True)
    assert [c.id for c in containers] == ["c1"]
    assert node.containers.get("c1").name == "web"
    assert node.images.list()[0].tags == ["nginx:latest"]
    assert node.volumes.get("vol1").attrs["Name"] == "vol1"
    assert node.networks.get("bridge").id == "net1"


def test_not_found_is_an_http_error(node):
    with pytest.raises(NodeApiError) as e:
        node.networks.get("missing")
    assert e.value.status_code == 404


def test_container_actions(node, remote_docker):
    container = node.containers.get("c1")
    container.start()
    container.reload()
    assert remote_docker.container.calls == ["start"]
    assert container.attrs["State"]["Running"] is True


def test_exec(node):
    result = node.containers.get("c1").exec_run(["echo", "hi there"])
    assert result.exit_code == 0
    assert result.output == b"ran echo 'hi there'"


def test_top(node, remote_docker):
    container = node.containers.get("c1")
    assert container.top() == {"Titles": ["PID", "CMD"], "Processes": [["1", "nginx"]]}
    container.top(ps_args="aux")
    assert remote_docker.container.calls == ["top None", "top aux"]


def test_top_route_errors(remote_app):
    headers = {"x-api-key": API_KEY}
    r = remote_app.get("/api/containers/localhost/containers/missing/top", headers=headers)
    assert r.status_code == 400


def test_logs(node):
    container = node.containers.get("c1")
    assert container.logs() == b"line one\nline two"
    assert list(container.logs(stream=True, follow=True)) == [b"line one\n", b"line two\n"]


def test_events(node):
    assert list(node.events(decode=True)) == [{"Type": "container", "Action": "start"}]


def test_unreachable_node():
    client = NodeContainerClient(base_url="http://127.0.0.1:9", timeout=1)
    with pytest.raises(NodeApiError) as e:
        client.ping()
    assert e.value.status_code == 502


def test_bootstrap_registers_nodes(monkeypatch):
    # don't connect to a docker daemon
    monkeypatch.setattr(ContainerClientsManager, "_connect", lambda self, name, url, test_ping=False: None)
    m = bootstrap_container_connection_manager(
        {
            "docker_hosts": {
                "node1": {"url": f"node+{NODE_URL}", "api_key": API_KEY},
                "node2": {"url": "node+http://node2:3080"},
            }
        }
    )
    assert isinstance(m.get("node1"), NodeContainerClient)
    assert m.urls()["node1"] == f"node+{NODE_URL}"
    assert set(m.nodes) == {"node1", "node2"}
    m.close_all()


def test_local_routes_use_node(remote_app, monkeypatch):
    """The local container routes work for a node like for a docker connection."""
    from mc import config
    from mc.plugin.containers import manager as manager_module
    from mc.plugin.containers.routes import router

    # the host list is cached on first use; start fresh so this test's config is used
    monkeypatch.setattr(manager_module, "CONTAINER_HOSTS", None)

    monkeypatch.setattr(
        config,
        "CONFIG",
        {
            "docker_hosts": {
                "node1": {"url": f"node+{NODE_URL}", "api_key": API_KEY, "autoconnect": True},
                "node2": {"url": "node+http://node2:3080"},
            }
        },
    )
    manager = ContainerClientsManager()
    manager.register("node1", make_node_client(remote_app), f"node+{NODE_URL}")

    app = FastAPI()
    app.state.ccm = manager
    app.include_router(router, prefix="/api")
    local = TestClient(app)

    # "connected" is deprecated and always true; the UI tracks connections itself
    hosts = {h["id"]: h for h in local.get("/api/containers/hosts").json()}
    assert set(hosts) == {"localhost", "node1", "node2"}
    assert hosts["node1"]["properties"] == {"engine": "node", "url": NODE_URL, "autoconnect": True}
    assert hosts["node2"]["properties"] == {"engine": "node", "url": "http://node2:3080", "autoconnect": False}
    assert hosts["localhost"]["properties"]["engine"] == "docker"

    assert [c["Id"] for c in local.get("/api/containers/node1/containers").json()] == ["c1"]
    r = local.post("/api/containers/node1/containers/c1/actions/start")
    assert r.status_code == 200, r.text
    r = local.get("/api/containers/node1/containers/c1/logs/stream")
    assert [line for line in r.text.splitlines() if line] == [
        '{"line": 1, "log": "line one\\n"}',
        '{"line": 2, "log": "line two\\n"}',
    ]
    assert local.get("/api/containers/node1/networks").json()[0]["Name"] == "bridge"


def test_ensure_is_safe_for_parallel_requests(monkeypatch):
    """Parallel first requests for a host create one client, not an 'already exists' error."""
    import threading
    import time

    created = []

    def slow_add(self, name, url, test_ping=False):
        time.sleep(0.05)
        client = object.__new__(NodeContainerClient)
        created.append(client)
        with self._lock:
            if name in self._clients:
                raise ValueError(f"Client '{name}' already exists")
            self._clients[name] = client
        return client

    monkeypatch.setattr(ContainerClientsManager, "_connect", slow_add)
    m = ContainerClientsManager()
    results, errors = [], []

    def worker():
        try:
            results.append(m.ensure("h1", "unix:///fake.sock"))
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(created) == 1
    assert all(r is created[0] for r in results)


def test_ensure_node_adds_prefix_once():
    m = ContainerClientsManager()
    m.ensure_node(NodeConfig(name="n1", url=NODE_URL))
    m.ensure_node(NodeConfig(name="n2", url=f"node+{NODE_URL}"))
    assert m.urls() == {"n1": f"node+{NODE_URL}", "n2": f"node+{NODE_URL}"}
    assert m.get("n2").base_url == NODE_URL


def test_connect_errors(monkeypatch):
    """Hosts must be connected first: unknown or unconnected hosts are 404, bad configs fail the connect with 400."""
    from fastapi import HTTPException

    from mc import config
    from mc.plugin.containers.deps import dep_container_connection
    from mc.plugin.containers.routes import connect_host

    monkeypatch.setattr(config, "CONFIG", {"docker_hosts": {
        "bad": {"url": "nope+tcp://x"},
        "node1": {"url": f"node+{NODE_URL}", "api_key": API_KEY},
    }})
    m = ContainerClientsManager()

    # requests don't connect on their own anymore
    for alias in ("unknown", "bad", "node1"):
        with pytest.raises(HTTPException) as e:
            dep_container_connection(alias, m)
        assert e.value.status_code == 404

    # 400, not 401: the UI logs out on 401
    for alias in ("unknown", "bad"):
        with pytest.raises(HTTPException) as e:
            connect_host(alias, m)
        assert e.value.status_code == 400
        assert not m.connected(alias)

    # connecting is idempotent and makes the host usable
    assert connect_host("node1", m) == {"id": "node1", "connected": True}
    assert connect_host("node1", m) == {"id": "node1", "connected": True}
    assert m.connected("node1")
    assert dep_container_connection("node1", m) is m.get("node1")


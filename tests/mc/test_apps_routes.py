"""
App spec API: create from scratch, read, list, update. Files land in temp MC_HOME / MC_CONFIG_DIR.
"""

import json
import sys

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mc import config
from mc.plugin.apps import apps_helper, routes

COMPOSE = "services:\n  web:\n    image: nginx:alpine\n"


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(apps_helper, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOST_HOME", "/host/home")
    monkeypatch.setattr(apps_helper, "MC_CONFIG_DIR", str(tmp_path / "etc"))
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    return TestClient(app)


def create(client, **overrides):
    body = {"id": "myapp", "title": "My App", "stackfile_content": COMPOSE, **overrides}
    return client.post("/api/apps/new/scratch", json=body)


def test_create_writes_spec_and_stackfile(client, tmp_path):
    r = create(client)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["spec"]["id"] == "myapp"
    assert data["spec"]["type"] == "compose"
    assert data["stackfile_content"] == COMPOSE

    spec_file = tmp_path / "etc" / "apps" / "myapp.yaml"
    assert yaml.safe_load(spec_file.read_text())["stackfile"] == "compose.yaml"
    assert (tmp_path / "home" / "apps" / "myapp" / "compose.yaml").read_text() == COMPOSE


def test_list_and_get(client):
    create(client)
    assert [s["id"] for s in client.get("/api/apps").json()] == ["myapp"]
    r = client.get("/api/apps/myapp")
    assert r.status_code == 200
    assert r.json()["spec"]["title"] == "My App"
    assert client.get("/api/apps/missing").status_code == 404


def test_create_rejects_duplicates_and_bad_input(client):
    assert create(client).status_code == 200
    assert create(client).status_code == 409
    assert create(client, id="Bad/Id").status_code == 400
    assert create(client, id="new").status_code == 400
    assert create(client, id="other", stackfile_content="services: [").status_code == 400
    assert create(client, id="other", stackfile_content="version: '3'\n").status_code == 400


def test_update(client, tmp_path):
    create(client)
    new_compose = "services:\n  web:\n    image: nginx:1.27\n"
    r = client.put("/api/apps/myapp", json={"title": "Renamed", "stackfile_content": new_compose})
    assert r.status_code == 200, r.text
    assert r.json()["spec"]["title"] == "Renamed"
    assert (tmp_path / "home" / "apps" / "myapp" / "compose.yaml").read_text() == new_compose

    # metadata-only update keeps the compose file
    r = client.put("/api/apps/myapp", json={"description": "desc"})
    assert r.json()["spec"]["title"] == "Renamed"
    assert r.json()["stackfile_content"] == new_compose

    assert client.put("/api/apps/myapp", json={"stackfile_content": "nope"}).status_code == 400
    assert client.put("/api/apps/missing", json={"title": "x"}).status_code == 404


def test_up_cmd_detaches_and_streams_plain_output(client, tmp_path):
    create(client)
    spec = apps_helper.load_app_spec("myapp")
    cmd, env = routes._action_cmd(spec, "up")

    app_dir = tmp_path / "home" / "apps" / "myapp"
    assert cmd[:4] == ["docker", "compose", "--project-directory", "/host/home/apps/myapp"]
    # saving generated the override files
    files = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "--file"]
    assert files == [str(app_dir / n) for n in ("compose.yaml", "compose.override.yaml", "compose.traefik.yaml")]
    up = cmd.index("up")
    assert cmd[up - 4:up] == ["--progress", "plain", "--ansi", "never"]
    assert {"--detach", "--remove-orphans", "--yes", "--no-color"} <= set(cmd[up + 1:])
    assert env["COMPOSE_PROJECT_NAME"] == "myapp"


def test_action_cmd_includes_existing_override_files(client, tmp_path):
    create(client)
    (tmp_path / "home" / "apps" / "myapp" / "compose.traefik.yaml").unlink()
    cmd, _ = routes._action_cmd(apps_helper.load_app_spec("myapp"), "down")
    assert cmd.count("--file") == 2
    assert cmd[cmd.index("down"):] == ["down", "--timeout", "60"]


def test_action_streams_output_and_return_code(client, monkeypatch):
    create(client)
    fake = [sys.executable, "-c", "print('pulling'); print('started')"]
    monkeypatch.setattr(routes, "_action_cmd", lambda spec, action: (fake, None))

    r = client.post("/api/apps/myapp/action/up")
    assert r.status_code == 200
    events = [json.loads(line) for line in r.text.splitlines() if line]
    assert events == [
        {"event": "STDOUT", "data": "pulling"},
        {"event": "STDOUT", "data": "started"},
        {"event": "RC", "data": "0"},
    ]


def test_action_rejects_bad_requests(client, tmp_path):
    assert client.post("/api/apps/missing/action/up").status_code == 404
    create(client)
    assert client.post("/api/apps/myapp/action/explode").status_code == 422
    (tmp_path / "home" / "apps" / "myapp" / "compose.yaml").unlink()
    assert client.post("/api/apps/myapp/action/up").status_code == 400


COMPOSE_WITH_RESOURCES = """services:
  web:
    image: nginx:alpine
    volumes: [data:/data]
volumes:
  data: {}
  cache: {}
networks:
  proxy:
    external: true
"""


def test_details_list_declared_compose_volumes_and_networks(client):
    r = create(client, stackfile_content=COMPOSE_WITH_RESOURCES)
    assert r.json()["compose_volumes"] == ["cache", "data"]
    assert r.json()["compose_networks"] == ["proxy"]


def test_update_volumes_and_networks(client, tmp_path):
    create(client)
    body = {
        "volumes": [
            {"volume_name": "data", "container_path": "/data", "bind": True, "host_path": "./data"},
            # host_path is dropped for named volumes
            {"volume_name": "cache", "container_path": "/cache", "host_path": "/ignored"},
        ],
        "networks": [{"network_name": "proxy", "external": True}],
    }
    r = client.put("/api/apps/myapp", json=body)
    assert r.status_code == 200, r.text
    spec = r.json()["spec"]
    assert spec["volumes"][0]["host_path"] == "./data"
    assert "host_path" not in spec["volumes"][1] or spec["volumes"][1]["host_path"] is None
    assert spec["networks"] == [{"network_name": "proxy", "external": True}]

    saved = yaml.safe_load((tmp_path / "etc" / "apps" / "myapp.yaml").read_text())
    assert [v["volume_name"] for v in saved["volumes"]] == ["data", "cache"]

    # omitting the lists keeps them
    r = client.put("/api/apps/myapp", json={"title": "x"})
    assert len(r.json()["spec"]["volumes"]) == 2


def test_create_with_volumes(client):
    r = create(client, volumes=[{"volume_name": "data", "container_path": "/data"}])
    assert r.status_code == 200, r.text
    assert r.json()["spec"]["volumes"][0]["volume_name"] == "data"


@pytest.mark.parametrize("volumes,networks", [
    ([{"volume_name": "data", "container_path": "relative"}], []),
    ([{"volume_name": "data", "container_path": "/data", "bind": True}], []),
    ([{"volume_name": "bad name", "container_path": "/data"}], []),
    ([{"volume_name": "data", "container_path": "/a"}, {"volume_name": "data", "container_path": "/b"}], []),
    ([], [{"network_name": "proxy"}, {"network_name": "proxy", "external": True}]),
    ([], [{"network_name": ""}]),
])
def test_invalid_volumes_and_networks_are_rejected(client, volumes, networks):
    create(client)
    r = client.put("/api/apps/myapp", json={"volumes": volumes, "networks": networks})
    assert r.status_code == 422, r.text
    assert isinstance(r.json()["detail"], list)
    # nothing was saved
    assert client.get("/api/apps/myapp").json()["spec"]["volumes"] == []
    # create rejects them too
    assert create(client, id="other", volumes=volumes, networks=networks).status_code == 422


def test_save_compiles_override(client, tmp_path):
    r = create(client, stackfile_content=COMPOSE_WITH_RESOURCES)
    assert r.json()["override_content"].startswith("# Generated by mc")
    body = {
        "volumes": [{"volume_name": "data", "container_path": "/data", "bind": True, "host_path": "./data"}],
        "networks": [{"network_name": "proxy", "external": True}],
    }
    r = client.put("/api/apps/myapp", json=body)
    assert r.json()["compile_warnings"] == []
    content = (tmp_path / "home" / "apps" / "myapp" / "compose.override.yaml").read_text()
    assert r.json()["override_content"] == content
    assert "volumes: !override" in content and "source: ./data" in content
    # GET returns the override but no warnings
    assert client.get("/api/apps/myapp").json()["override_content"] == content


def test_save_returns_compile_warnings(client):
    compose = "services:\n  a:\n    image: x\n  b:\n    image: y\n"
    r = create(client, stackfile_content=compose, volumes=[{"volume_name": "data", "container_path": "/data"}])
    assert r.status_code == 200
    assert "isn't mounted by any service" in r.json()["compile_warnings"][0]


class FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def test_compiled_lists_files_and_merged_config(client, monkeypatch):
    create(client, volumes=[{"volume_name": "data", "container_path": "/data"}])
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FakeCompleted(stdout="name: myapp\nservices: {}\n")

    monkeypatch.setattr(routes.subprocess, "run", fake_run)
    r = client.get("/api/apps/myapp/compiled")
    assert r.status_code == 200, r.text
    data = r.json()
    assert [f["name"] for f in data["files"]] == ["compose.yaml", "compose.override.yaml", "compose.traefik.yaml"]
    assert data["files"][0]["content"] == COMPOSE
    assert "!override" in data["files"][1]["content"]
    assert data["merged"] == "name: myapp\nservices: {}\n"
    assert data["merged_error"] is None
    assert calls[0][-1] == "config" and calls[0].count("--file") == 3


def test_compiled_reports_compose_errors(client, monkeypatch):
    create(client)
    monkeypatch.setattr(routes.subprocess, "run", lambda cmd, **kw: FakeCompleted(1, stderr="bad stuff\n"))
    data = client.get("/api/apps/myapp/compiled").json()
    assert data["merged"] is None
    assert data["merged_error"] == "bad stuff"

    def missing(cmd, **kw):
        raise FileNotFoundError()

    monkeypatch.setattr(routes.subprocess, "run", missing)
    assert client.get("/api/apps/myapp/compiled").json()["merged_error"] == "docker CLI not found"
    assert client.get("/api/apps/missing/compiled").status_code == 404

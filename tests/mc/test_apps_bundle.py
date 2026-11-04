"""
Apps from bundles (tar archives): extraction safety, API create / update, CLI.
Files land in temp MC_HOME / MC_CONFIG_DIR.
"""

import io
import tarfile

import pytest
import yaml
from click.testing import CliRunner
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mc import config
from mc.cli import apps as cli_apps
from mc.plugin.apps import apps_bundle, apps_helper, routes
from mc.plugin.apps.apps_bundle import BundleError, ExtractedBundle

COMPOSE = "services:\n  web:\n    image: nginx:alpine\n    volumes:\n      - ./conf/nginx.conf:/etc/nginx/nginx.conf:ro\n"


def make_bundle(files: dict[str, str], prefix: str = "", extra=None) -> bytes:
    """tar.gz bytes with the given {path: content}; `extra(tar)` can add special entries."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(prefix + path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        if extra:
            extra(tar)
    return buf.getvalue()


BUNDLE = {"compose.yaml": COMPOSE, "conf/nginx.conf": "events {}\n"}


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(apps_helper, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOST_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(apps_helper, "MC_CONFIG_DIR", str(tmp_path / "etc"))
    return tmp_path


@pytest.fixture
def client(home) -> TestClient:
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    return TestClient(app)


def upload(client, data: bytes, app_id="myapp", **form):
    return client.post("/api/apps/new/bundle", data={"id": app_id, **form},
                       files={"bundle": ("app.tar.gz", data, "application/gzip")})


# ----------------------------- extraction --------------------------------- #

def test_extract_finds_stackfile_and_files():
    with ExtractedBundle(io.BytesIO(make_bundle(BUNDLE))) as b:
        assert b.stackfile == "compose.yaml"
        assert b.files() == ["compose.yaml", "conf/nginx.conf"]


def test_extract_strips_single_top_level_folder():
    with ExtractedBundle(io.BytesIO(make_bundle(BUNDLE, prefix="myapp-1.0/"))) as b:
        assert b.files() == ["compose.yaml", "conf/nginx.conf"]


def test_extract_skips_macos_metadata():
    files = {**BUNDLE, "._myapp": "x", "myapp/._compose.yaml": "x", "myapp/.DS_Store": "x"}
    files = {k if k.startswith(("._", "myapp/")) else "myapp/" + k: v for k, v in files.items()}
    with ExtractedBundle(io.BytesIO(make_bundle(files))) as b:
        assert b.files() == ["compose.yaml", "conf/nginx.conf"]


@pytest.mark.parametrize("name", ["docker-compose.yml", "compose.yml"])
def test_extract_other_stackfile_names(name):
    with ExtractedBundle(io.BytesIO(make_bundle({name: COMPOSE}))) as b:
        assert b.stackfile == name


def _symlink(tar):
    info = tarfile.TarInfo("evil")
    info.type = tarfile.SYMTYPE
    info.linkname = "/etc/passwd"
    tar.addfile(info)


@pytest.mark.parametrize("files,extra,message", [
    ({"README.md": "hi"}, None, "no compose file"),
    ({"compose.yaml": COMPOSE, "../escape.txt": "x"}, None, "outside the app folder"),
    ({"compose.yaml": COMPOSE, "/abs.txt": "x"}, None, "outside the app folder"),
    ({"compose.yaml": COMPOSE}, _symlink, "links aren't allowed"),
    ({"compose.yaml": COMPOSE, "compose.override.yaml": "services: {}\n"}, None, "mc generates it"),
])
def test_extract_rejects(files, extra, message):
    with pytest.raises(BundleError, match=message):
        ExtractedBundle(io.BytesIO(make_bundle(files, extra=extra)))


def test_extract_rejects_non_tar():
    with pytest.raises(BundleError, match="Not a tar archive"):
        ExtractedBundle(io.BytesIO(b"definitely not a tarball"))


def test_extract_rejects_too_many_files(monkeypatch):
    monkeypatch.setattr(apps_bundle, "MAX_BUNDLE_FILES", 2)
    with pytest.raises(BundleError, match="more than 2 entries"):
        ExtractedBundle(io.BytesIO(make_bundle({**BUNDLE, "x": "y"})))


def test_extract_rejects_too_large(monkeypatch):
    monkeypatch.setattr(apps_bundle, "MAX_BUNDLE_SIZE", 10)
    with pytest.raises(BundleError, match="larger than"):
        ExtractedBundle(io.BytesIO(make_bundle(BUNDLE)))


# ----------------------------- API ---------------------------------------- #

def test_api_create_from_bundle(client, home):
    r = upload(client, make_bundle(BUNDLE), title="My App")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["spec"]["stackfile"] == "compose.yaml"
    assert data["spec"]["title"] == "My App"
    assert data["stackfile_content"] == COMPOSE
    app_dir = home / "home" / "apps" / "myapp"
    assert (app_dir / "conf" / "nginx.conf").read_text() == "events {}\n"
    assert (app_dir / "compose.override.yaml").is_file()  # compiled
    assert (home / "etc" / "apps" / "myapp.yaml").is_file()


def test_api_create_from_bundle_errors(client):
    assert upload(client, make_bundle({"README.md": "x"})).status_code == 400
    assert upload(client, make_bundle({"compose.yaml": "services: {}\n"})).status_code == 400
    assert upload(client, make_bundle(BUNDLE), app_id="Bad/Id").status_code == 400
    assert upload(client, make_bundle(BUNDLE)).status_code == 200
    assert upload(client, make_bundle(BUNDLE)).status_code == 409


def test_api_update_from_bundle_keeps_spec_and_other_files(client, home):
    assert upload(client, make_bundle(BUNDLE)).status_code == 200
    r = client.put("/api/apps/myapp", json={"environment": {"A": "1"}})
    assert r.status_code == 200, r.text
    app_dir = home / "home" / "apps" / "myapp"
    (app_dir / "data").mkdir()
    (app_dir / "data" / "keep.txt").write_text("user data")

    new_compose = "services:\n  web:\n    image: nginx:1.27\n"
    bundle = make_bundle({"docker-compose.yml": new_compose, "conf/nginx.conf": "events { worker_connections 8; }\n"})
    r = client.put("/api/apps/myapp/bundle", files={"bundle": ("app.tgz", bundle, "application/gzip")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["spec"]["stackfile"] == "docker-compose.yml"
    assert data["spec"]["environment"] == {"A": "1"}
    assert data["stackfile_content"] == new_compose
    assert "worker_connections" in (app_dir / "conf" / "nginx.conf").read_text()
    assert (app_dir / "data" / "keep.txt").read_text() == "user data"


def test_api_update_from_bundle_errors(client, home):
    bundle = make_bundle(BUNDLE)
    r = client.put("/api/apps/missing/bundle", files={"bundle": ("app.tgz", bundle, "application/gzip")})
    assert r.status_code == 404
    assert upload(client, bundle).status_code == 200
    # a folder in the app dir where the bundle has a file: nothing is written
    (home / "home" / "apps" / "myapp" / "extra.txt").mkdir()
    bad = make_bundle({"compose.yaml": "services:\n  x:\n    image: y\n", "extra.txt": "x"})
    r = client.put("/api/apps/myapp/bundle", files={"bundle": ("app.tgz", bad, "application/gzip")})
    assert r.status_code == 400
    assert (home / "home" / "apps" / "myapp" / "compose.yaml").read_text() == COMPOSE


# ----------------------------- CLI ---------------------------------------- #

@pytest.fixture
def run(home):
    runner = CliRunner()

    def _run(*args, **kwargs):
        return runner.invoke(cli_apps.apps, list(args), catch_exceptions=False, **kwargs)
    return _run


def test_cli_create_and_update_from_bundle(run, home):
    path = home / "app.tar.gz"
    path.write_bytes(make_bundle(BUNDLE))
    r = run("create", "myapp", "-b", str(path))
    assert r.exit_code == 0, r.output
    app_dir = home / "home" / "apps" / "myapp"
    assert (app_dir / "conf" / "nginx.conf").is_file()

    path.write_bytes(make_bundle({"compose.yml": "services:\n  web:\n    image: nginx:1.27\n"}))
    r = run("update", "myapp", "-b", str(path))
    assert r.exit_code == 0, r.output
    spec = yaml.safe_load((home / "etc" / "apps" / "myapp.yaml").read_text())
    assert spec["stackfile"] == "compose.yml"


def test_cli_update_compose_file(run, home):
    assert run("create", "myapp", "-f", "-", input=COMPOSE).exit_code == 0
    r = run("update", "myapp", "-f", "-", input="services:\n  api:\n    image: x\n")
    assert r.exit_code == 0, r.output
    assert "api:" in (home / "home" / "apps" / "myapp" / "compose.yaml").read_text()


def test_cli_needs_exactly_one_source(run, home):
    assert run("create", "myapp").exit_code == 2
    path = home / "app.tar.gz"
    path.write_bytes(make_bundle(BUNDLE))
    assert run("create", "myapp", "-b", str(path), "-f", "-", input=COMPOSE).exit_code == 2
    path.write_bytes(make_bundle({"README.md": "x"}))
    r = run("create", "myapp", "-b", str(path))
    assert r.exit_code == 1
    assert "no compose file" in r.output

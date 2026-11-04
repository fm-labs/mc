"""
`mc apps` CLI on top of the app specs. Files land in temp MC_HOME / MC_CONFIG_DIR.
"""

import pytest
import yaml
from click.testing import CliRunner

from mc import config
from mc.cli import apps as cli_apps
from mc.plugin.apps import apps_helper

COMPOSE = "services:\n  web:\n    image: nginx:alpine\n    expose: [80]\n"


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr(apps_helper, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(config, "MC_HOST_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(apps_helper, "MC_CONFIG_DIR", str(tmp_path / "etc"))
    runner = CliRunner()

    def _run(*args, **kwargs):
        return runner.invoke(cli_apps.apps, list(args), catch_exceptions=False, **kwargs)
    return _run


@pytest.fixture
def ran(monkeypatch):
    """Capture compose subprocess calls instead of running docker."""
    calls = []

    class Result:
        returncode = 0

    def fake_run(cmd, env=None, **kwargs):
        calls.append((cmd, env))
        return Result()
    monkeypatch.setattr(cli_apps.subprocess, "run", fake_run)
    return calls


def create(run, app_id="myapp"):
    r = run("create", app_id, "-f", "-", "--title", "My App", input=COMPOSE)
    assert r.exit_code == 0, r.output
    return r


def test_create_list_show(run, tmp_path):
    r = create(run)
    assert "Created" in r.output
    assert (tmp_path / "home" / "apps" / "myapp" / "compose.override.yaml").is_file()

    assert "myapp" in run("list").output
    assert "already exists" in run("create", "myapp", "-f", "-", input=COMPOSE).output
    assert run("create", "Bad Id", "-f", "-", input=COMPOSE).exit_code == 1
    assert "YAML mapping" in run("create", "x", "-f", "-", input="nope").output

    out = run("show", "myapp").output
    assert "title: My App" in out
    assert run("show", "missing").exit_code == 1


def test_list_empty(run):
    assert "No apps" in run("list").output


def test_env_set_list_unset(run, tmp_path):
    create(run)
    # TOKEN alone prompts for a hidden value
    r = run("env", "set", "myapp", "PORT=8080", "TOKEN", input="s3cret\n")
    assert r.exit_code == 0, r.output
    assert apps_helper.load_app_spec("myapp").environment == {"PORT": "8080", "TOKEN": "s3cret"}

    assert run("env", "list", "myapp").output.splitlines() == ["PORT=****", "TOKEN=****"]
    assert "TOKEN=s3cret" in run("env", "list", "myapp", "--show-values").output
    # values hidden in show too
    assert "s3cret" not in run("show", "myapp").output

    r = run("env", "set", "myapp", "DOCKER_HOST=tcp://x")
    assert r.exit_code == 1 and "set by mc" in r.output

    run("env", "unset", "myapp", "TOKEN", "NOPE")
    assert apps_helper.load_app_spec("myapp").environment == {"PORT": "8080"}


def test_up_compiles_and_runs_compose(run, ran, tmp_path):
    create(run)
    spec = apps_helper.load_app_spec("myapp")
    spec.routing = [apps_helper.AppRoutingSpec(service_name="web", service_port=80, domain_names=["a.example.com"])]
    apps_helper.save_app_spec(spec)  # saved without compiling

    r = run("up", "myapp")
    assert r.exit_code == 0, r.output
    cmd, env = ran[0]
    assert "up" in cmd and "--detach" in cmd
    assert env["COMPOSE_PROJECT_NAME"] == "myapp"
    traefik = (tmp_path / "home" / "apps" / "myapp" / "compose.traefik.yaml").read_text()
    assert "a.example.com" in traefik


def test_up_no_compile(run, ran, tmp_path):
    create(run)
    spec = apps_helper.load_app_spec("myapp")
    spec.routing = [apps_helper.AppRoutingSpec(service_name="web", service_port=80, domain_names=["a.example.com"])]
    apps_helper.save_app_spec(spec)
    run("up", "myapp", "--no-compile")
    assert "a.example.com" not in (tmp_path / "home" / "apps" / "myapp" / "compose.traefik.yaml").read_text()


@pytest.mark.parametrize("action", ["down", "stop", "restart"])
def test_other_actions(run, ran, action):
    create(run)
    assert run(action, "myapp").exit_code == 0
    assert action in ran[0][0]


def test_action_exit_code_is_passed_through(run, monkeypatch):
    create(run)

    class Failed:
        returncode = 3
    monkeypatch.setattr(cli_apps.subprocess, "run", lambda cmd, env=None: Failed())
    assert run("down", "myapp").exit_code == 3


def test_config_runs_compose_config(run, ran):
    create(run)
    run("config", "myapp")
    assert ran[0][0][-1] == "config"


def test_compile_prints_warnings(run):
    create(run)
    spec = apps_helper.load_app_spec("myapp")
    spec.routing = [apps_helper.AppRoutingSpec(service_name="nope", service_port=80, domain_names=["a.example.com"])]
    apps_helper.save_app_spec(spec)
    r = run("compile", "myapp")
    assert r.exit_code == 0
    assert "nope" in r.output and "compose.traefik.yaml" in r.output


def test_edit_spec(run, monkeypatch, tmp_path):
    create(run)

    def editor(text, **kwargs):
        data = yaml.safe_load(text)
        data["routing"] = [{"service_name": "web", "service_port": 80, "domain_names": ["b.example.com"]}]
        return yaml.safe_dump(data)
    monkeypatch.setattr(cli_apps.click, "edit", editor)
    r = run("edit", "myapp")
    assert r.exit_code == 0, r.output
    assert apps_helper.load_app_spec("myapp").routing[0].domain_names == ["b.example.com"]
    assert "b.example.com" in (tmp_path / "home" / "apps" / "myapp" / "compose.traefik.yaml").read_text()


def test_edit_invalid_then_give_up(run, monkeypatch):
    create(run)
    monkeypatch.setattr(cli_apps.click, "edit", lambda text, **kw: text + "routing: [{service_port: 0}]\n")
    r = run("edit", "myapp", input="n\n")
    assert r.exit_code == 1
    assert "Invalid app spec" in r.output
    assert apps_helper.load_app_spec("myapp").routing == []


def test_edit_rejects_id_change_and_no_changes(run, monkeypatch):
    create(run)
    monkeypatch.setattr(cli_apps.click, "edit", lambda text, **kw: text.replace("id: myapp", "id: other"))
    assert "can't be changed" in run("edit", "myapp", input="n\n").output
    monkeypatch.setattr(cli_apps.click, "edit", lambda text, **kw: None)
    assert "No changes" in run("edit", "myapp").output


def test_edit_compose(run, monkeypatch, tmp_path):
    create(run)
    monkeypatch.setattr(cli_apps.click, "edit", lambda text, **kw: text.replace("nginx:alpine", "nginx:1.27"))
    assert run("edit", "myapp", "--compose").exit_code == 0
    assert "nginx:1.27" in (tmp_path / "home" / "apps" / "myapp" / "compose.yaml").read_text()

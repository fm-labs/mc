"""
compose.override.yaml generation from app spec volume / network overrides.
"""

import shutil
import subprocess

import pytest
import yaml

from mc.plugin.apps.apps_helper import AppNetworkSpec, AppSpec, AppVolumeSpec
from mc.plugin.apps.compose_override import OverrideDict, OverrideList, build_override, dump_override, parse_mount

STACK = yaml.safe_load("""
services:
  web:
    image: nginx:alpine
    volumes:
      - data:/var/lib/data:ro
      - ./conf:/etc/conf
    networks: [front]
  worker:
    image: alpine
    volumes:
      - type: volume
        source: data
        target: /data
  host:
    image: alpine
    network_mode: host
volumes:
  data: {}
networks:
  front: {}
""")


def spec(volumes=(), networks=()) -> AppSpec:
    return AppSpec(id="t", type="compose", stackfile="compose.yaml",
                   volumes=list(volumes), networks=list(networks))


@pytest.mark.parametrize("entry,expected", [
    ("data:/data", ("data", "/data", False)),
    ("data:/data:ro", ("data", "/data", True)),
    ("./x:/x:rw,z", ("./x", "/x", False)),
    ("/anon", (None, "/anon", False)),
    ({"source": "data", "target": "/d", "read_only": True}, ("data", "/d", True)),
])
def test_parse_mount(entry, expected):
    assert parse_mount(entry) == expected


def test_no_overrides_is_empty():
    assert build_override(spec(), STACK) == ({"services": {}}, [])


def test_bind_volume_replaces_every_mount_of_the_volume():
    vol = AppVolumeSpec(volume_name="data", container_path="/srv", bind=True, host_path="./data")
    override, warnings = build_override(spec([vol]), STACK)
    assert warnings == []
    web = override["services"]["web"]["volumes"]
    assert isinstance(web, OverrideList)
    assert web == [
        {"type": "bind", "source": "./data", "target": "/srv", "bind": {"create_host_path": True}, "read_only": True},
        "./conf:/etc/conf",  # other mounts are kept
    ]
    assert override["services"]["worker"]["volumes"][0]["source"] == "./data"
    assert "volumes" not in override  # bind mounts don't declare a named volume


def test_named_volume_is_declared():
    vol = AppVolumeSpec(volume_name="data", container_path="/data")
    override, _ = build_override(spec([vol]), STACK)
    assert override["volumes"] == {"data": {}}
    assert override["services"]["worker"]["volumes"] == [{"type": "volume", "source": "data", "target": "/data"}]


def test_unused_volume_goes_to_the_only_service_or_warns():
    vol = AppVolumeSpec(volume_name="cache", container_path="/cache")
    single = {"services": {"app": {"image": "x"}}}
    override, warnings = build_override(spec([vol]), single)
    assert override["services"]["app"]["volumes"] == [{"type": "volume", "source": "cache", "target": "/cache"}]
    assert warnings == []

    override, warnings = build_override(spec([vol]), STACK)
    assert override == {"services": {}}
    assert "cache" in warnings[0]


def test_networks_join_all_services_and_keep_existing():
    nets = [AppNetworkSpec(network_name="proxy", external=True), AppNetworkSpec(network_name="back")]
    override, warnings = build_override(spec(networks=nets), STACK)
    assert override["networks"] == {"proxy": {"external": True}, "back": {}}
    assert isinstance(override["networks"]["proxy"], OverrideDict)
    assert override["services"]["web"]["networks"] == {"front": {}, "proxy": {}, "back": {}}
    # a service without networks keeps the default network
    assert override["services"]["worker"]["networks"] == {"default": {}, "proxy": {}, "back": {}}
    assert "host" not in override["services"]
    assert "network_mode" in warnings[0]


def test_dump_uses_override_tags():
    vol = AppVolumeSpec(volume_name="data", container_path="/data")
    net = AppNetworkSpec(network_name="proxy", external=True)
    text = dump_override(build_override(spec([vol], [net]), STACK)[0])
    assert "volumes: !override" in text
    assert "networks: !override" in text
    assert "proxy: !override" in text


@pytest.mark.skipif(not shutil.which("docker"), reason="docker CLI not installed")
def test_docker_compose_accepts_generated_override(tmp_path):
    (tmp_path / "compose.yaml").write_text(yaml.safe_dump(STACK))
    vol = AppVolumeSpec(volume_name="data", container_path="/srv", bind=True, host_path="./data")
    net = AppNetworkSpec(network_name="proxy", external=True)
    (tmp_path / "compose.override.yaml").write_text(dump_override(build_override(spec([vol], [net]), STACK)[0]))

    r = subprocess.run(
        ["docker", "compose", "--project-directory", str(tmp_path), "-p", "t",
         "-f", str(tmp_path / "compose.yaml"), "-f", str(tmp_path / "compose.override.yaml"),
         "config", "--format", "json"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 and "Unknown" in r.stderr:
        pytest.skip(f"docker compose too old: {r.stderr}")
    assert r.returncode == 0, r.stderr
    config = yaml.safe_load(r.stdout)
    web = config["services"]["web"]
    assert [(v["type"], v["target"]) for v in web["volumes"]] == [("bind", "/srv"), ("bind", "/etc/conf")]
    assert set(web["networks"]) == {"front", "proxy"}
    assert set(config["services"]["worker"]["networks"]) == {"default", "proxy"}
    assert config["networks"]["proxy"]["external"] is True

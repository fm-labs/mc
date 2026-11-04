"""
compose.traefik.yaml generation from app spec routes.
"""

import shutil
import subprocess

import pydantic
import pytest
import yaml

from mc.plugin.apps.apps_helper import AppNetworkSpec, AppRoutingSpec, AppSpec, compose_container_ports
from mc.plugin.apps.compose_override import (
    OverrideDict,
    TRAEFIK_NETWORK_NAME,
    build_override,
    build_traefik_override,
    dump_override,
)

STACK = yaml.safe_load("""
services:
  web:
    image: nginx:alpine
    labels: ["com.example.keep=1"]
    networks: [front]
    ports: ["8080:80", "127.0.0.1:8443:443/tcp"]
  admin.ui:
    image: nginx:alpine
    expose: [3000]
  host:
    image: alpine
    network_mode: host
networks:
  front: {}
""")


def spec(routing=(), networks=()) -> AppSpec:
    return AppSpec(id="myapp", type="compose", stackfile="compose.yaml",
                   routing=list(routing), networks=list(networks))


def route(service="web", port=80, mode="http", domains=("example.com",)) -> AppRoutingSpec:
    return AppRoutingSpec(service_name=service, container_port=port, mode=mode, domain_names=list(domains))


def test_no_routes_is_empty():
    assert build_traefik_override(spec(), STACK) == ({"services": {}}, [])


def test_http_route_labels_and_network():
    override, warnings = build_traefik_override(spec([route(domains=["a.example.com", "b.example.com"])]), STACK)
    assert warnings == []
    web = override["services"]["web"]
    assert web["labels"] == {
        "traefik.enable": "true",
        "traefik.docker.network": TRAEFIK_NETWORK_NAME,
        "traefik.http.services.myapp-web-80.loadbalancer.server.port": "80",
        "traefik.http.routers.myapp-web-80-http.rule": "Host(`a.example.com`) || Host(`b.example.com`)",
        "traefik.http.routers.myapp-web-80-http.entrypoints": "web",
        "traefik.http.routers.myapp-web-80-http.service": "myapp-web-80",
    }
    # keeps the service's own networks
    assert isinstance(web["networks"], OverrideDict)
    assert set(web["networks"]) == {"front", TRAEFIK_NETWORK_NAME}
    assert override["networks"] == {TRAEFIK_NETWORK_NAME: {"external": True}}


def test_https_and_both_modes():
    labels = build_traefik_override(spec([route(mode="https")]), STACK)[0]["services"]["web"]["labels"]
    assert "traefik.http.routers.myapp-web-80-http.rule" not in labels
    assert labels["traefik.http.routers.myapp-web-80-https.entrypoints"] == "websecure"
    assert labels["traefik.http.routers.myapp-web-80-https.tls"] == "true"
    assert labels["traefik.http.routers.myapp-web-80-https.tls.certresolver"] == "le"

    labels = build_traefik_override(spec([route(mode="http+https")]), STACK)[0]["services"]["web"]["labels"]
    assert "traefik.http.routers.myapp-web-80-http.rule" in labels
    assert "traefik.http.routers.myapp-web-80-https.rule" in labels


def test_two_ports_on_one_service_and_dots_in_names():
    override, _ = build_traefik_override(spec([
        route(port=80), route(port=443, domains=["secure.example.com"]),
        route(service="admin.ui", port=3000, domains=["admin.example.com"]),
    ]), STACK)
    web = override["services"]["web"]["labels"]
    assert web["traefik.http.routers.myapp-web-443-http.service"] == "myapp-web-443"
    assert web["traefik.http.services.myapp-web-80.loadbalancer.server.port"] == "80"
    admin = override["services"]["admin.ui"]
    assert "traefik.http.routers.myapp-admin-ui-3000-http.rule" in admin["labels"]
    # no networks in compose.yaml means it was on `default`
    assert set(admin["networks"]) == {"default", TRAEFIK_NETWORK_NAME}


def test_includes_spec_networks():
    override, _ = build_traefik_override(spec([route()], [AppNetworkSpec(network_name="db")]), STACK)
    assert set(override["services"]["web"]["networks"]) == {"front", "db", TRAEFIK_NETWORK_NAME}


def test_unknown_and_network_mode_services_warn():
    override, warnings = build_traefik_override(spec([route(service="nope"), route(service="host")]), STACK)
    assert override == {"services": {}}
    assert len(warnings) == 2


@pytest.mark.parametrize("kwargs", [
    {"container_port": 0},
    {"container_port": 70000},
    {"service_name": "bad name"},
    {"domain_names": []},
    {"domain_names": ["  "]},
    {"domain_names": ["*.example.com"]},
    {"domain_names": ["exa mple.com"]},
    {"mode": "tcp"},
])
def test_invalid_routes(kwargs):
    with pytest.raises(pydantic.ValidationError):
        AppRoutingSpec(**{"service_name": "web", "container_port": 80, "domain_names": ["example.com"], **kwargs})


def test_domains_are_normalized():
    r = route(domains=[" Example.COM. ", "example.com", "", "b.example.com"])
    assert r.domain_names == ["example.com", "b.example.com"]


def test_duplicate_routes_rejected():
    with pytest.raises(pydantic.ValidationError):
        spec([route(), route(domains=["other.example.com"])])


def test_compose_container_ports():
    assert compose_container_ports(STACK) == {"web": [80, 443], "admin.ui": [3000], "host": []}
    assert compose_container_ports({"services": {"x": {"ports": [{"target": 81}, 82, "1000-1001:9000-9001"]}}}) \
        == {"x": [81, 82, 9000]}
    assert compose_container_ports(None) == {}


@pytest.mark.skipif(not shutil.which("docker"), reason="docker CLI not installed")
def test_docker_compose_accepts_traefik_override(tmp_path):
    s = spec([route(mode="http+https")], [AppNetworkSpec(network_name="db", external=True)])
    (tmp_path / "compose.yaml").write_text(yaml.safe_dump(STACK))
    (tmp_path / "compose.override.yaml").write_text(dump_override(build_override(s, STACK)[0]))
    (tmp_path / "compose.traefik.yaml").write_text(dump_override(build_traefik_override(s, STACK)[0]))

    r = subprocess.run(
        ["docker", "compose", "--project-directory", str(tmp_path), "-p", "t",
         *[a for f in ("compose.yaml", "compose.override.yaml", "compose.traefik.yaml")
           for a in ("-f", str(tmp_path / f))],
         "config", "--format", "json"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 and "Unknown" in r.stderr:
        pytest.skip(f"docker compose too old: {r.stderr}")
    assert r.returncode == 0, r.stderr
    config = yaml.safe_load(r.stdout)
    web = config["services"]["web"]
    assert set(web["networks"]) == {"front", "db", TRAEFIK_NETWORK_NAME}
    # base labels are kept
    assert web["labels"]["com.example.keep"] == "1"
    assert web["labels"]["traefik.http.routers.myapp-web-80-https.tls"] == "true"
    assert config["networks"][TRAEFIK_NETWORK_NAME]["external"] is True
    assert "traefik.enable" not in config["services"]["admin.ui"].get("labels", {})

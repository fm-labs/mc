import shlex
import logging

from mc.docker.compose import Compose, Service
from mc.util.dockercli_helper import dockercli

logger = logging.getLogger(__name__)

def build_traefik_service(
    network_name: str = "traefik-ssl",
    traefik_version: str = "v3.6.2",
    enable_dashboard: bool = False,
    dashboard_insecure: bool = False,
    enable_letsencrypt: bool = True,
    letsencrypt_email: str = "acme@example.org",
    enable_socket_proxy: bool = True,
    enable_https_redirect: bool = True,
    enable_security_headers: bool = True,
    log_level: str = "INFO",
) -> Service:
    labels = [
        "traefik.enable=true",
        f"traefik.docker.network={network_name}",
    ]

    if enable_dashboard:
        labels += [
            "traefik.http.middlewares.admin-auth.basicauth.users"
            "=${TRAEFIK_DASHBOARD_ADMIN_USER?Variable not set}:${TRAEFIK_DASHBOARD_ADMIN_PASSWORD?Variable not set}",
            "traefik.http.routers.traefik-dashboard-https.middlewares=admin-auth",
        ]

    if enable_security_headers:
        labels += [
            "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000",
            "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true",
            "traefik.http.middlewares.security-headers.headers.stsPreload=true",
            "traefik.http.middlewares.security-headers.headers.frameDeny=true",
            "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true",
            "traefik.http.middlewares.security-headers.headers.referrerPolicy=no-referrer",
            "traefik.http.middlewares.security-headers.headers.customResponseHeaders.Server=",
            "traefik.http.middlewares.security-headers.headers.customResponseHeaders.X-Powered-By=",
        ]

    docker_endpoint = (
        "tcp://socket-proxy:2375" if enable_socket_proxy else "unix:///var/run/docker.sock"
    )

    command = [
        "--api",
        f"--api.dashboard={str(enable_dashboard).lower()}",
        f"--api.insecure={str(dashboard_insecure).lower()}",
        "--providers.docker",
        "--providers.docker.exposedbydefault=false",
        f"--providers.docker.endpoint={docker_endpoint}",
        "--entrypoints.web.address=:80",
        "--entrypoints.websecure.address=:443",
    ]

    if enable_https_redirect:
        command += [
            "--entrypoints.web.http.redirections.entryPoint.to=websecure",
            "--entrypoints.web.http.redirections.entryPoint.scheme=https",
            "--entrypoints.web.http.redirections.entryPoint.permanent=true",
        ]

    if enable_security_headers:
        command += [
            "--entrypoints.websecure.http.middlewares=security-headers@docker",
        ]

    if enable_letsencrypt:
        command += [
            f"--certificatesresolvers.le.acme.email={letsencrypt_email}",
            "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json",
            "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web",
        ]

    command += [
        "--accesslog=true",
        "--accesslog.format=common",
        "--log",
        f"--log.level={log_level}",
        "--log.format=common",
        "--log.nocolor=true",
    ]

    return Service(
        name="traefik",
        image=f"traefik:{traefik_version}",
        labels=labels,
        command=command,
        networks=[network_name],
        volumes=["traefik_letsencrypt:/letsencrypt"] if enable_letsencrypt else None,
        ports=["80:80", "443:443", "8080:8080"],
        restart="always",
    )


def build_socket_proxy_service(
    network_name: str = "traefik-ssl",
    socket_proxy_version: str = "latest",
) -> Service:
    return Service(
        name="socket-proxy",
        image=f"tecnativa/docker-socket-proxy:{socket_proxy_version}",
        networks=[network_name],
        volumes=["/var/run/docker.sock:/var/run/docker.sock:ro"],
        restart="always",
        environment={"CONTAINERS": "1", "SERVICES": "1", "LABELS": "1"},
        expose=["2375"],
    )


def build_traefik_compose(
    network_name: str = "traefik-ssl",
    traefik_version: str = "v3.6.2",
    enable_dashboard: bool = False,
    dashboard_insecure: bool = False,
    enable_letsencrypt: bool = True,
    letsencrypt_email: str = "acme@example.org",
    enable_socket_proxy: bool = True,
    enable_https_redirect: bool = True,
    enable_security_headers: bool = True,
    log_level: str = "INFO",
) -> Compose:
    services = [
        build_traefik_service(
            network_name=network_name,
            traefik_version=traefik_version,
            enable_dashboard=enable_dashboard,
            dashboard_insecure=dashboard_insecure,
            enable_letsencrypt=enable_letsencrypt,
            letsencrypt_email=letsencrypt_email,
            enable_socket_proxy=enable_socket_proxy,
            enable_https_redirect=enable_https_redirect,
            enable_security_headers=enable_security_headers,
            log_level=log_level,
        )
    ]

    if enable_socket_proxy:
        services.append(build_socket_proxy_service(network_name=network_name))

    return Compose(
        services=services,
        networks={network_name: {"external": True}},
        volumes={"traefik_letsencrypt": None} if enable_letsencrypt else None,
    )


def run_traefik_proxy_compose():
    """Launch docker container with traefik reverse proxy"""

    compose = build_traefik_compose(
        network_name="traefik",
        enable_dashboard=True,
        enable_letsencrypt=True,
        letsencrypt_email="admin@example.com",
        log_level="WARNING",
    )
    print(compose.to_compose_yaml())


def run_traefik_proxy_container():
    """Launch docker container with traefik reverse proxy using docker run"""

    service = build_traefik_service(
        network_name="default",
        traefik_version="v3.6.2",
        enable_dashboard=False,
        dashboard_insecure=False,
        enable_letsencrypt=False,
        letsencrypt_email="admin@example.org",
        enable_socket_proxy=False,
        enable_https_redirect=False,
        enable_security_headers=False,
        log_level="INFO",
    )
    docker_cmd = service.to_docker_cmd(detach=True)
    res = dockercli(shlex.split(docker_cmd))
    if res["rc"] != 0:
        logger.error(f"Exited with code {res['rc']}: {res['stderr']}")
    else:
        logger.info(f"Traefik proxy container started successfully: {res['stdout']}")

from __future__ import annotations

import threading
from typing import Dict, Iterable, Optional, Any

from docker import DockerClient
from podman import PodmanClient

from mc.client.apiclient import McApiClient
from mc.inventory.storage import get_inventory_storage_instance

ContainerClient = PodmanClient | DockerClient


class NodeContainerClient:

    class Containers:
        def list(self, *args, **kwargs):
            return []

    class Volumes:
        def list(self, *args, **kwargs):
            return []

    class Images:
        def list(self, *args, **kwargs):
            return []

    def __init__(self, name: str, base_url: str) -> None:
        self.name = name
        self.client = McApiClient(api_url=base_url, api_key="")
        self.node_alias = "localdocker"

    def _get(self, endpoint: str) -> Optional[dict]:
        try:
            return self.client.get(f"/containers/{self.node_alias}/{endpoint}")
        except Exception as e:
            print(f"Error getting df from container client '{self.name}': {e}")
            return None

    def ping(self) -> Any:
        return self._get("ping")

    def version(self) -> Any:
        return self._get("version")

    def df(self) -> Any:
        return self._get("df")

    @property
    def containers(self) -> Any:
        return self.Containers()

    @property
    def images(self) -> Any:
        return self.Images()

    @property
    def volumes(self) -> Any:
        return self.Volumes()


class ContainerClientsManager:
    def __init__(self) -> None:
        self._clients: Dict[str, ContainerClient] = {}
        self._urls: Dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, name: str) -> Optional[ContainerClient]:
        return self._clients.get(name)

    def names(self) -> Iterable[str]:
        return tuple(self._clients.keys())

    def urls(self) -> Dict[str, str]:
        """
        Return a dict of client names and their base URLs.
        """
        return self._urls

    def add(self, name: str, base_url: str, test_ping: bool = False) -> ContainerClient:
        with self._lock:
            if name in self._clients:
                raise ValueError(f"Client '{name}' already exists")

            # split base_url into engine and url
            if "+" in base_url:
                engine, url = base_url.split("+", 1)
            else:
                engine, url = "docker", base_url  # default to docker if no engine specified

            if engine == "docker":
                use_ssh = url.startswith("ssh")
                c = DockerClient(base_url=url, timeout=15, use_ssh_client=use_ssh)
            elif engine == "podman":
                c = PodmanClient(base_url=url, timeout=10)
            else:
                raise ValueError(f"Unknown container engine '{engine}' in URL '{base_url}'")

            try:
                if test_ping:
                    c.ping(timeout=10)
            except Exception:
                c.close()
                raise

            print(f"Added container client '{name}' with URL '{base_url}'")
            self._clients[name] = c
            self._urls[name] = base_url
            return c

    def ensure(self, name: str, base_url: str, test_ping: bool = True) -> ContainerClient:
        existing = self.get(name)
        if existing:
            return existing
        return self.add(name, base_url, test_ping)

    def remove(self, name: str, close: bool = True) -> bool:
        with self._lock:
            c = self._clients.pop(name, None)
            if not c:
                return False
            if close:
                try: c.close()
                except Exception: pass
            self._urls.pop(name, None)
            return True

    def close_all(self) -> None:
        with self._lock:
            for c in list(self._clients.values()):
                try: c.close()
                except Exception: pass
            self._clients.clear()
            self._urls.clear()


#@lru_cache(maxsize=1)
#def init_container_connection_manager() -> ContainerClientsManager:
#    return ContainerClientsManager()


def bootstrap_container_connection_manager() -> ContainerClientsManager:
    """Idempotent: make sure defaults exist (read from env/config if you like)."""
    m = ContainerClientsManager()
    m.ensure("localdocker", "unix://var/run/docker.sock", test_ping=False)

    # storage = get_inventory_storage_instance()
    # items = storage.list_items("mc_node")
    # for item in items:
    #     name = item.get("id")
    #     url = item.get("url")
    #     autoconnect = True # item.get("autoconnect", False)
    #     print(f"Found container host in inventory: {name} at {url} (autoconnect={autoconnect})")
    #     if autoconnect:
    #         try:
    #             m._clients.update({name: NodeContainerClient(name, url)})
    #         except Exception as e:
    #             print(f"Failed to connect to container host '{name}' at '{url}':", e)

    # inventory = get_inventory_storage_instance()
    # items = inventory.list_items("container_host")
    # for item in items:
    #     url = item.get("url")
    #     engine = item.get("engine", "docker").lower()
    #     autoconnect = item.get("autoconnect", False)
    #     print("CCM: Found container host in inventory:", engine, url)
    #     if not autoconnect:
    #         print("CCM: Skipping container host (autoconnect is false):", url)
    #         continue
    #
    #     engine_url = engine + "+" + url
    #     try:
    #         if engine == "docker" or engine == "podman":
    #             m.ensure(item.get("name", url), engine_url, test_ping=False)
    #             print("CCM: Configured container host:", engine_url)
    #         else:
    #             print(f"CCM: Unknown container engine '{engine}' for host '{url}'")
    #     except Exception as e:
    #         print(f"CCM: Failed to configure container host '{url}': {e}")
    #m.ensure("local", "unix:///run/podman/podman.sock", test_ping=False)
    return m


# best-effort cleanup if the process exits without FastAPI shutdown
#atexit.register(lambda: asyncio.run(init_container_connection_manager().close_all()))

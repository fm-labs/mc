from __future__ import annotations

import threading
from typing import Dict, Iterable, Optional

from docker import DockerClient
from podman import PodmanClient


class ContainerClientsManager:
    def __init__(self) -> None:
        self._clients: Dict[str, PodmanClient|DockerClient] = {}
        self._urls: Dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, name: str) -> Optional[PodmanClient|DockerClient]:
        return self._clients.get(name)

    def names(self) -> Iterable[str]:
        return tuple(self._clients.keys())

    def urls(self) -> Dict[str, str]:
        """
        Return a dict of client names and their base URLs.
        """
        return self._urls

    def add(self, name: str, base_url: str, test_ping: bool = False) -> PodmanClient|DockerClient:
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

    def ensure(self, name: str, base_url: str, test_ping: bool = True) -> PodmanClient|DockerClient:
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

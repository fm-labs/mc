# manager.py
from __future__ import annotations
import asyncio, atexit
from functools import lru_cache
from typing import Dict, Iterable, Optional

from docker import DockerClient
from podman import PodmanClient

from mc.inventory.storage import get_inventory_storage_instance


class ContainerClientsManager:
    def __init__(self) -> None:
        self._clients: Dict[str, PodmanClient|DockerClient] = {}
        self._urls: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    def get(self, name: str) -> Optional[PodmanClient|DockerClient]:
        return self._clients.get(name)

    def names(self) -> Iterable[str]:
        return tuple(self._clients.keys())

    def urls(self) -> Dict[str, str]:
        """
        Return a dict of client names and their base URLs.
        """
        return self._urls

    async def add(self, name: str, base_url: str, test_ping: bool = True) -> PodmanClient|DockerClient:
        async with self._lock:
            if name in self._clients:
                raise ValueError(f"Client '{name}' already exists")

            # split base_url into engine and url
            if "+" in base_url:
                engine, url = base_url.split("+", 1)
            else:
                engine, url = "podman", base_url  # default to podman

            if engine == "docker":
                use_ssh = url.startswith("ssh")
                c = DockerClient(base_url=url, timeout=15, use_ssh_client=use_ssh)
            elif engine == "podman":
                c = PodmanClient(base_url=url, timeout=10)
            else:
                raise ValueError(f"Unknown container engine '{engine}' in URL '{base_url}'")

            try:
                if test_ping:
                    c.ping()
            except Exception:
                c.close()
                raise

            print(f"Added container client '{name}' with URL '{base_url}'")
            self._clients[name] = c
            self._urls[name] = base_url
            return c

    async def ensure(self, name: str, base_url: str, test_ping: bool = True) -> PodmanClient|DockerClient:
        existing = self.get(name)
        if existing:
            return existing
        return await self.add(name, base_url, test_ping)

    async def remove(self, name: str, close: bool = True) -> bool:
        async with self._lock:
            c = self._clients.pop(name, None)
            if not c:
                return False
            if close:
                try: c.close()
                except Exception: pass
            self._urls.pop(name, None)
            return True

    async def close_all(self) -> None:
        async with self._lock:
            for c in list(self._clients.values()):
                try: c.close()
                except Exception: pass
            self._clients.clear()
            self._urls.clear()


@lru_cache(maxsize=1)
def get_container_connection_manager() -> ContainerClientsManager:
    return ContainerClientsManager()


async def bootstrap_container_connection_manager() -> None:
    """Idempotent: make sure defaults exist (read from env/config if you like)."""
    m = get_container_connection_manager()

    inventory = get_inventory_storage_instance()
    items = inventory.list_items("container_host")
    for item in items:
        url = item.get("properties", {}).get("url")
        engine = item.get("properties", {}).get("engine", "docker").lower()
        autoconnect = item.get("properties", {}).get("autoconnect", False)
        print("CCM: Found container host in inventory:", engine, url)
        if not autoconnect:
            print("CCM: Skipping container host (autoconnect is false):", url)
            continue

        # check if we have a host inventory record
        # if url.startswith("ssh://"):
        #     hostname = url.split("://")[-1].split("/")[0]
        #     print("CCM: Lookup host inventory record for:", hostname)
        #     host = inventory.get_item_by_name("host", hostname)
        #     if host:
        #         print("  Found host inventory record:", host.get("name"))
        #         #ssh_hostname = host.get("properties", {}).get("ssh_hostname", hostname)
        #         ssh_hostname = hostname
        #         ssh_port = host.get("properties", {}).get("ssh_port", 22)
        #         ssh_user = host.get("properties", {}).get("ssh_user", "")
        #         #ssh_key_name = host.get("properties", {}).get("ssh_key_name", "")
        #
        #         url = f"ssh://"
        #         if ssh_user:
        #             url += f"{ssh_user}@"
        #         url += f"{ssh_hostname}"
        #         if ssh_port and ssh_port != 22:
        #             url += f":{ssh_port}"
        #         print("  Updated container host URL to:", url)
        #     else:
        #         print("  No host inventory record found for:", hostname)

        engine_url = engine + "+" + url
        try:
            if engine == "docker" or engine == "podman":
                await m.ensure(item.get("name", url), engine_url, test_ping=False)
                print("CCM: Configured container host:", engine_url)
            else:
                print(f"CCM: Unknown container engine '{engine}' for host '{url}'")
        except Exception as e:
            print(f"CCM: Failed to configure container host '{url}': {e}")

    #await m.ensure("local", "unix:///run/podman/podman.sock", test_ping=False)


# best-effort cleanup if the process exits without FastAPI shutdown
atexit.register(lambda: asyncio.run(get_container_connection_manager().close_all()))

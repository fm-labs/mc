# This is a utility module for WireGuard
# It provides functions to manage WireGuard configurations and keys.
# It includes functions to generate keys, create configurations, and manage peers.
# It also includes functions to start and stop the WireGuard interface.
# It uses the subprocess module to interact with the WireGuard command line tools.
# It uses the os and pathlib module to manage file paths and permissions.
# Use dataclasses lib to represent WireGuard configurations and peers.
import os
import subprocess
from pathlib import Path
from typing import List, Optional

# --- dataclasses for WireGuard configurations and peers ---
from dataclasses import dataclass, field

# @dataclass
# class WireGuardInterface:
#     private_key: str
#     address: List[str]
#     listen_port: Optional[int] = None
#     dns: Optional[List[str]] = None


@dataclass
class WireGuardPeer:
    public_key: str
    allowed_ips: List[str]
    endpoint: Optional[str] = None
    persistent_keepalive: Optional[int] = None


@dataclass
class WireGuardConfig:
    private_key: str
    address: List[str]
    listen_port: Optional[int] = None
    dns: Optional[List[str]] = None
    peers: List[WireGuardPeer] = field(default_factory=list)
    post_up: Optional[str] = None
    post_down: Optional[str] = None

    def add_peer(self, peer: WireGuardPeer):
        """Add a peer to the WireGuard configuration."""
        self.peers.append(peer)

    def remove_peer(self, public_key: str):
        """Remove a peer from the WireGuard configuration by public key."""
        self.peers = [peer for peer in self.peers if peer.public_key != public_key]

    def clear_peers(self):
        """Remove all peers from the WireGuard configuration."""
        self.peers.clear()

    def add_dns(self, dns: List[str]):
        """Add DNS servers to the WireGuard configuration."""
        if self.dns is None:
            self.dns = []
        self.dns.extend(dns)

    def remove_dns(self, dns: List[str]):
        """Remove DNS servers from the WireGuard configuration."""
        if self.dns is not None:
            self.dns = [d for d in self.dns if d not in dns]
            if not self.dns:
                self.dns = None

    def clear_dns(self):
        """Remove all DNS servers from the WireGuard configuration."""
        self.dns = None

    def save_to_file(self, path: Path):
        """Save WireGuard configuration to file."""
        config_str = self.to_string()
        with open(path, 'w') as f:
            f.write(config_str)
        os.chmod(path, 0o600)  # Set file permissions to be readable and writable only by the owner

    @staticmethod
    def load_from_file(path: Path) -> 'WireGuardConfig':
        """Load WireGuard configuration from file."""
        with open(path, 'r') as f:
            lines = f.readlines()

        private_key = ""
        address = []
        listen_port = None
        dns = []
        peers = []
        post_up = None
        post_down = None

        current_peer = None

        for line in lines:
            line = line.strip()
            if line.startswith("[Interface]"):
                continue
            elif line.startswith("[Peer]"):
                if current_peer:
                    peers.append(current_peer)
                current_peer = WireGuardPeer(public_key="", allowed_ips=[])
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                if key == "PrivateKey":
                    private_key = value
                elif key == "Address":
                    address = [ip.strip() for ip in value.split(",")]
                elif key == "ListenPort":
                    listen_port = int(value)
                elif key == "DNS":
                    dns = [d.strip() for d in value.split(",")]
                elif key == "PostUp":
                    post_up = value
                elif key == "PostDown":
                    post_down = value
                elif key == "PublicKey" and current_peer is not None:
                    current_peer.public_key = value
                elif key == "AllowedIPs" and current_peer is not None:
                    current_peer.allowed_ips = [ip.strip() for ip in value.split(",")]
                elif key == "Endpoint" and current_peer is not None:
                    current_peer.endpoint = value
                elif key == "PersistentKeepalive" and current_peer is not None:
                    current_peer.persistent_keepalive = int(value)

        if current_peer:
            peers.append(current_peer)

        return WireGuardConfig(
            private_key=private_key,
            address=address,
            listen_port=listen_port,
            dns=dns if dns else None,
            peers=peers,
            post_up=post_up,
            post_down=post_down,
        )

    def to_dict(self) -> dict:
        """Convert the WireGuard configuration to a dictionary format."""
        return {
            "Interface": {
                "PrivateKey": self.private_key,
                "Address": self.address,
                "ListenPort": self.listen_port,
                "DNS": self.dns,
                "PostUp": self.post_up,
                "PostDown": self.post_down,
            },
            "Peers": [
                {
                    "PublicKey": peer.public_key,
                    "AllowedIPs": peer.allowed_ips,
                    "Endpoint": peer.endpoint,
                    "PersistentKeepalive": peer.persistent_keepalive,
                }
                for peer in self.peers
            ],
        }

    def to_string(self) -> str:
        """Convert the WireGuard configuration to a string format."""
        config_lines = [
            "[Interface]",
            f"PrivateKey = {self.private_key}",
        ]
        if self.address:
            config_lines.append(f"Address = {', '.join(self.address)}")
        if self.listen_port:
            config_lines.append(f"ListenPort = {self.listen_port}")
        if self.dns:
            config_lines.append(f"DNS = {', '.join(self.dns)}")
        if self.post_up:
            config_lines.append(f"PostUp = {self.post_up}")
        if self.post_down:
            config_lines.append(f"PostDown = {self.post_down}")

        for peer in self.peers:
            config_lines.append("\n[Peer]")
            config_lines.append(f"PublicKey = {peer.public_key}")
            if peer.endpoint:
                config_lines.append(f"Endpoint = {peer.endpoint}")
            if peer.allowed_ips:
                config_lines.append(f"AllowedIPs = {', '.join(peer.allowed_ips)}")
            if peer.persistent_keepalive is not None:
                config_lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

        return "\n".join(config_lines)


def wg_genkey() -> str:
    """Generate a WireGuard private key."""
    result = subprocess.run(['wg', 'genkey'], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to generate key: {result.stderr}")
    return result.stdout.strip()


def wg_pubkey(private_key: str) -> str:
    """Generate a WireGuard public key from a private key."""
    result = subprocess.run(['wg', 'pubkey'], input=private_key, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to generate public key: {result.stderr}")
    return result.stdout.strip()


def wg_genkey_pair() -> tuple[str, str]:
    """Generate a WireGuard key pair (private and public keys)."""
    private_key = wg_genkey()
    public_key = wg_pubkey(private_key)
    return private_key, public_key

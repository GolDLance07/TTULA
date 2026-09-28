"""Tailscale Adapter for TTULA.

Wraps Tailscale CLI (`tailscale status --json`, `tailscale ip`, `tailscale netcheck`),
discovers nodes, and manages explicit local authorization for lab targets.
"""

from __future__ import annotations
import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from ttula.core.models import ExecutionNode, Target
from ttula.execution.process import run_process_command

logger = logging.getLogger("ttula.integrations.tailscale")


class TailscaleAdapter:
    """Manages Tailscale network status and device discovery."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        tailscale_bin: str = "tailscale",
        mock_mode: bool = False,
    ):
        self.tailscale_bin = tailscale_bin
        self.mock_mode = mock_mode
        self.config_path = Path(
            config_path
            or os.environ.get(
                "TTULA_CONFIG_DIR",
                str(Path.home() / ".config" / "ttula"),
            )
        )
        self.auth_file = self.config_path / "authorized_targets.json"
        self._authorized_targets_cache: Dict[str, bool] = {}
        self._load_authorized_targets()

    def _load_authorized_targets(self) -> None:
        """Loads explicitly authorized targets from local config."""
        if self.auth_file.exists():
            try:
                with open(self.auth_file, "r", encoding="utf-8") as f:
                    self._authorized_targets_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read authorized targets config: {e}")
                self._authorized_targets_cache = {}
        else:
            self._authorized_targets_cache = {}

    def save_lab_authorization(self, target_name_or_ip: str, authorized: bool) -> None:
        """Saves authorization status explicitly to local configuration."""
        self._authorized_targets_cache[target_name_or_ip] = authorized
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            with open(self.auth_file, "w", encoding="utf-8") as f:
                json.dump(self._authorized_targets_cache, f, indent=2)
            logger.info(f"Target '{target_name_or_ip}' authorization updated: {authorized}")
        except Exception as e:
            logger.error(f"Failed to persist target authorization: {e}")

    def is_authorized(self, identifier: str) -> bool:
        """Returns True if and only if explicitly configured as authorized."""
        return self._authorized_targets_cache.get(identifier, False)

    def get_status_raw(self) -> Dict[str, Any]:
        """Fetches raw JSON status from tailscale daemon."""
        if self.mock_mode:
            return self._get_mock_status()

        res = run_process_command([self.tailscale_bin, "status", "--json"], tool_name="tailscale")
        if not res.success or not res.stdout.strip():
            logger.warning(f"Tailscale status call returned non-zero ({res.exit_code}): {res.stderr}")
            # If tailscale binary not found or daemon not running, check if mock fallback is permitted
            return self._get_fallback_status(error_msg=res.stderr or "Tailscale daemon unreachable")

        try:
            return json.loads(res.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Tailscale JSON: {e}")
            return self._get_fallback_status(error_msg=f"JSON parse error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Provides parsed status summary."""
        raw = self.get_status_raw() or {}
        self_node = raw.get("Self") or {}
        backend_state = raw.get("BackendState") or "Unknown"
        is_online = backend_state in ("Running", "Connected")

        devices = []
        # Current node
        if self_node:
            my_ips = self_node.get("TailscaleIPs") or []
            devices.append({
                "name": self_node.get("HostName") or "local-node",
                "ip": my_ips[0] if my_ips else "127.0.0.1",
                "os": self_node.get("OS") or "",
                "online": bool(self_node.get("Online", True)),
                "is_self": True,
                "is_authorized_lab": False,
            })

        # Peer nodes
        peers = raw.get("Peer") or {}
        if isinstance(peers, dict):
            for _, peer in peers.items():
                if not isinstance(peer, dict):
                    continue
                ips = peer.get("TailscaleIPs") or []
                ip = ips[0] if ips else ""
                hname = peer.get("HostName") or peer.get("DNSName") or "peer"
                auth = self.is_authorized(hname) or (bool(ip) and self.is_authorized(ip))
                devices.append({
                    "name": hname,
                    "ip": ip,
                    "os": peer.get("OS") or "",
                    "online": bool(peer.get("Online", False)),
                    "is_self": False,
                    "is_authorized_lab": auth,
                })

        return {
            "online": is_online,
            "backend_state": backend_state,
            "self_ip": devices[0]["ip"] if devices else "",
            "device_count": len(devices),
            "devices": devices,
        }

    def get_targets(self) -> List[Target]:
        """Extracts Target objects from Tailscale peers."""
        status = self.get_status()
        targets: List[Target] = []
        for dev in status.get("devices", []):
            if dev.get("is_self"):
                continue  # skip self
            name = dev["name"]
            ip = dev["ip"]
            is_lab = self.is_authorized(name) or self.is_authorized(ip)
            targets.append(
                Target(
                    name=name,
                    tailscale_ip=ip,
                    is_authorized_lab=is_lab,
                    hostname=name,
                    os=dev.get("os", ""),
                )
            )
        return targets

    def get_execution_node(self) -> ExecutionNode:
        """Returns the local execution node representing this machine."""
        status = self.get_status()
        self_ip = status.get("self_ip", "127.0.0.1")
        return ExecutionNode(
            name="kali-thinkpad",
            local=True,
            capabilities=["bash", "nmap", "legba", "tookie", "uro", "tailscale"],
            tailscale_ip=self_ip,
            status="online" if status.get("online") else "offline",
        )

    def run_netcheck(self) -> Dict[str, Any]:
        """Executes tailscale netcheck."""
        if self.mock_mode:
            return {"udp": True, "derp": "fra", "latency_ms": 28.5}

        res = run_process_command([self.tailscale_bin, "netcheck"], tool_name="tailscale")
        return {
            "success": res.success,
            "output": res.stdout or res.stderr,
        }

    def _get_fallback_status(self, error_msg: str) -> Dict[str, Any]:
        return {
            "BackendState": "Stopped",
            "Self": {"HostName": "local-kali", "TailscaleIPs": ["127.0.0.1"], "Online": False},
            "Peer": {},
            "error": error_msg,
        }

    def _get_mock_status(self) -> Dict[str, Any]:
        return {
            "BackendState": "Running",
            "Self": {
                "HostName": "kali-thinkpad",
                "TailscaleIPs": ["100.64.0.1"],
                "OS": "linux",
                "Online": True,
            },
            "Peer": {
                "peer-1": {
                    "HostName": "lab-vulnerable-server",
                    "TailscaleIPs": ["100.64.0.50"],
                    "OS": "linux",
                    "Online": True,
                },
                "peer-2": {
                    "HostName": "personal-phone",
                    "TailscaleIPs": ["100.64.0.99"],
                    "OS": "android",
                    "Online": True,
                },
            },
        }

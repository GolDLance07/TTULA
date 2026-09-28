"""Legba Authentication Testing Adapter for TTULA.

Builds strictly validated Legba commands for credential and authentication testing.
MANDATORY SAFETY: Strictly gated on Target.is_authorized_lab == True.
"""

from __future__ import annotations
import logging
import shutil
from typing import Dict, List, Optional
from ttula.core.models import Command, Target

logger = logging.getLogger("ttula.integrations.legba")


class LegbaAdapter:
    """Generates structured Legba commands with strict safety gates."""

    SUPPORTED_PROTOCOLS = [
        "ssh",
        "http",
        "smb",
        "ftp",
        "telnet",
        "mysql",
        "postgres",
        "rdp",
        "vnc",
        "smtp",
    ]

    SAFETY_WARNINGS = [
        "CAUTION: Authentication testing can trigger account lockouts and IDS alerts.",
        "Ensure the target is explicitly listed in your authorized lab inventory.",
        "Default concurrency is throttled to prevent lab service exhaustion.",
    ]

    def __init__(self, legba_bin: Optional[str] = None):
        self.legba_bin = legba_bin or shutil.which("legba") or "legba"

    def get_supported_protocols(self) -> List[str]:
        return list(self.SUPPORTED_PROTOCOLS)

    def get_safety_warnings(self) -> List[str]:
        return list(self.SAFETY_WARNINGS)

    def build_command(
        self,
        protocol: str,
        target: Target,
        username: str = "",
        password: str = "",
        wordlist_user: str = "",
        wordlist_pass: str = "",
        port: Optional[int] = None,
        concurrency: int = 2,
        extra_flags: Optional[List[str]] = None,
    ) -> Command:
        """Builds a validated Command object for Legba.
        
        Security gates:
        1. target MUST be a Target instance.
        2. target.is_authorized_lab MUST be True.
        3. protocol must be in SUPPORTED_PROTOCOLS.
        """
        if not isinstance(target, Target):
            raise TypeError("target must be an instance of Target.")

        if not target.validate_lab_authorization():
            raise PermissionError(
                f"SAFETY GATE TRIGGERED: Target '{target.name}' ({target.tailscale_ip}) "
                "is NOT marked as an authorized lab! Legba command creation is strictly prohibited."
            )

        proto = protocol.lower().strip()
        if proto not in self.SUPPORTED_PROTOCOLS:
            raise ValueError(f"Protocol '{protocol}' is not supported by Legba adapter.")

        # Ensure conservative concurrency
        safe_concurrency = max(1, min(concurrency, 10))

        # Build argv list
        argv: List[str] = [self.legba_bin, proto]

        # Target specification
        if proto == "http":
            target_url = target.tailscale_ip
            if not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = f"http://{target_url}"
            if port:
                target_url = f"{target_url}:{port}"
            argv.extend(["--target", target_url])
        else:
            argv.extend(["--target", target.tailscale_ip])
            if port:
                argv.extend(["--port", str(port)])

        # Credentials / Wordlists
        if username:
            argv.extend(["--username", username])
        elif wordlist_user:
            argv.extend(["--wordlist-user", wordlist_user])

        if password:
            argv.extend(["--password", password])
        elif wordlist_pass:
            argv.extend(["--wordlist-pass", wordlist_pass])

        # Concurrency
        argv.extend(["-c", str(safe_concurrency)])

        if extra_flags:
            argv.extend(extra_flags)

        title = f"Legba {proto.upper()} Auth Test [{target.name}]"
        desc = (
            f"Target: {target.tailscale_ip}:{port or 'default'} | Protocol: {proto} | "
            f"Concurrency: {safe_concurrency}"
        )

        return Command(
            source_tool="legba",
            title=title,
            description=desc,
            argv=argv,
            target=target,
            requires_authorized_lab=True,
        )

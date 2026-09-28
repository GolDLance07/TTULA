"""Core Data Models for TTULA.

Defines the primary data structures that flow between core engine,
adapters, and execution manager.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Target:
    """Represents a remote or local target device on the tailnet."""
    name: str
    tailscale_ip: str
    is_authorized_lab: bool = False
    hostname: str = ""
    os: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate_lab_authorization(self) -> bool:
        """Strict check to verify target is authorized for testing."""
        return self.is_authorized_lab is True


@dataclass
class ExecutionNode:
    """Represents an execution environment (e.g. local Kali ThinkPad)."""
    name: str
    local: bool = True
    capabilities: List[str] = field(default_factory=list)
    tailscale_ip: str = "127.0.0.1"
    status: str = "online"


@dataclass
class Command:
    """Structured command representation.
    
    Security rule: MUST be an argv list, NEVER a raw shell string.
    """
    source_tool: str
    title: str
    description: str
    argv: List[str]
    target: Optional[Target] = None
    placeholders: Dict[str, str] = field(default_factory=dict)
    requires_authorized_lab: bool = False

    def __post_init__(self):
        if not isinstance(self.argv, list):
            raise TypeError("Command.argv must be a list of strings, never a raw string.")
        for i, arg in enumerate(self.argv):
            if not isinstance(arg, str):
                raise TypeError(f"Command.argv[{i}] must be a str, got {type(arg)}")

    @property
    def display_string(self) -> str:
        """Formatted preview string for operator display with shell quoting."""
        import shlex
        return " ".join(shlex.quote(arg) for arg in self.argv)


@dataclass
class Operation:
    """Represents a security operation category and associated target."""
    name: str
    category: str
    target: Optional[Target] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class URLCollection:
    """Structured collection of URLs from discovery or processing tools."""
    items: List[str]
    source_tool: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.items)


@dataclass
class ToolResult:
    """Result returned by execution manager or adapter."""
    tool: str
    stdout: str
    stderr: str = ""
    exit_code: int = 0
    structured_data: Any = None
    duration_seconds: float = 0.0

    @property
    def success(self) -> bool:
        return self.exit_code == 0


@dataclass
class TerminalSession:
    """Represents an interactive PTY or shell session."""
    id: str
    node: ExecutionNode
    pty_fd: Optional[int] = None
    alive: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    history: List[str] = field(default_factory=list)

"""Operation and Command Template Mapping for TTULA.

Maps operations/categories to candidate commands and handles safe placeholder
substitution using explicit Target and Node values.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from ttula.core.models import Command, Operation, Target, ExecutionNode


class OperationRegistry:
    """Registry of known operations and categories."""

    DEFAULT_CATEGORIES = [
        "service_enumeration",
        "web_reconnaissance",
        "credential_testing",
        "osint_discovery",
        "network_inspection",
    ]

    def __init__(self):
        self._operations: Dict[str, Operation] = {}
        self._init_defaults()

    def _init_defaults(self):
        defaults = [
            Operation(
                name="service_enumeration",
                category="enumeration",
                tags=["nmap", "scan", "port", "service", "enumeration"],
                description="Port and service discovery against authorized lab targets",
            ),
            Operation(
                name="web_reconnaissance",
                category="recon",
                tags=["web", "http", "tookie", "uro", "urls", "crawler"],
                description="Web endpoint and OSINT discovery",
            ),
            Operation(
                name="credential_testing",
                category="auth",
                tags=["legba", "auth", "bruteforce", "login", "credentials"],
                description="Controlled authentication testing against authorized targets",
            ),
            Operation(
                name="network_inspection",
                category="network",
                tags=["tailscale", "ping", "netcheck", "routing"],
                description="Tailscale network health and node connectivity checks",
            ),
        ]
        for op in defaults:
            self.register(op)

    def register(self, operation: Operation) -> None:
        self._operations[operation.name] = operation

    def list_operations(self) -> List[Operation]:
        return list(self._operations.values())

    def get_by_category(self, category: str) -> List[Operation]:
        return [op for op in self._operations.values() if op.category == category]

    def find_by_tag(self, tag: str) -> List[Operation]:
        tag_lower = tag.lower()
        return [
            op for op in self._operations.values()
            if any(tag_lower in t.lower() for t in op.tags)
        ]


def fill_command_placeholders(
    command: Command,
    target: Optional[Target] = None,
    execution_node: Optional[ExecutionNode] = None,
    extra_params: Optional[Dict[str, str]] = None,
) -> Command:
    """Safely fills command placeholders in argv list.
    
    Security rules:
    - Never uses raw shell string evaluation.
    - Token-level replacement inside argv elements.
    - If command requires an authorized lab, target MUST have is_authorized_lab=True.
    """
    if command.requires_authorized_lab:
        if not target or not target.validate_lab_authorization():
            raise PermissionError(
                f"Command '{command.title}' requires an authorized lab target. "
                f"Target '{getattr(target, 'name', 'None')}' is not authorized."
            )

    substitutions: Dict[str, str] = {}

    if target:
        substitutions["<target>"] = target.tailscale_ip or target.name
        substitutions["<ip>"] = target.tailscale_ip
        substitutions["<host>"] = target.tailscale_ip
        substitutions["<hostname>"] = target.hostname or target.name

    if execution_node:
        substitutions["<node>"] = execution_node.name
        substitutions["<local_ip>"] = execution_node.tailscale_ip

    if extra_params:
        for k, v in extra_params.items():
            key_tag = f"<{k}>" if not (k.startswith("<") and k.endswith(">")) else k
            substitutions[key_tag] = str(v)

    new_argv: List[str] = []
    filled_placeholders: Dict[str, str] = dict(command.placeholders)

    for arg in command.argv:
        new_arg = arg
        for ph, val in substitutions.items():
            if ph in new_arg:
                new_arg = new_arg.replace(ph, val)
                filled_placeholders[ph] = val
        new_argv.append(new_arg)

    return Command(
        source_tool=command.source_tool,
        title=command.title,
        description=command.description,
        argv=new_argv,
        target=target,
        placeholders=filled_placeholders,
        requires_authorized_lab=command.requires_authorized_lab,
    )

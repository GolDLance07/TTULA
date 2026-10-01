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
    
    Supports both:
    - Arsenal-NG {{variable}} and {{variable|default}} tokens
    - Legacy <target>, <port> placeholders
    
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
    var_map: Dict[str, str] = {}

    if target:
        target_ip = target.tailscale_ip or target.name
        substitutions["<target>"] = target_ip
        substitutions["<ip>"] = target.tailscale_ip
        substitutions["<host>"] = target.tailscale_ip
        substitutions["<rhost>"] = target.tailscale_ip
        substitutions["<hostname>"] = target.hostname or target.name

        var_map["target"] = target_ip
        var_map["ip"] = target.tailscale_ip
        var_map["host"] = target.tailscale_ip
        var_map["rhost"] = target.tailscale_ip
        var_map["hostname"] = target.hostname or target.name
        var_map["target_range"] = target.tailscale_ip

    if execution_node:
        substitutions["<node>"] = execution_node.name
        substitutions["<local_ip>"] = execution_node.tailscale_ip
        var_map["node"] = execution_node.name
        var_map["lhost"] = execution_node.tailscale_ip

    if extra_params:
        for k, v in extra_params.items():
            val_str = str(v).strip()
            clean_k = k.strip().lower()
            key_tag = f"<{clean_k}>" if not (clean_k.startswith("<") and clean_k.endswith(">")) else clean_k
            
            # Don't overwrite an existing non-empty value (like target IP) with an empty string
            if val_str or key_tag not in substitutions:
                substitutions[key_tag] = val_str
            if val_str or clean_k.strip("<>") not in var_map:
                var_map[clean_k.strip("<>")] = val_str


    # Provide safe fallback values for generic placeholders if not supplied
    default_fallbacks = {
        "<port>": "22" if any("ssh" in str(a).lower() for a in command.argv) else "80",
        "<username>": "admin",
        "<password>": "admin",
        "<wordlist>": "/usr/share/wordlists/dirb/common.txt",
    }
    for ph_key, ph_default in default_fallbacks.items():
        if ph_key not in substitutions:
            substitutions[ph_key] = ph_default
            var_map[ph_key.strip("<>")] = ph_default

    # Ensure URL is synthesized if target & port are known
    if "url" not in var_map:
        t_ip = var_map.get("target") or var_map.get("ip", "127.0.0.1")
        t_port = var_map.get("port", "80")
        var_map["url"] = f"http://{t_ip}:{t_port}"
        substitutions["<url>"] = var_map["url"]

    re_arsenal_ph = re.compile(r"\{\{\s*([^}|]+)(?:\|([^}]*))?\s*\}\}")

    new_argv: List[str] = []
    filled_placeholders: Dict[str, str] = dict(command.placeholders)

    for arg in command.argv:
        new_arg = arg
        # 1. Replace legacy <...> placeholders
        for ph, val in substitutions.items():
            if ph in new_arg:
                new_arg = new_arg.replace(ph, val)
                filled_placeholders[ph] = val

        # 2. Replace Arsenal-NG {{variable|default}} placeholders
        def _replace_ph(m: re.Match) -> str:
            v_name = m.group(1).strip()
            v_default = m.group(2).strip() if m.group(2) is not None else ""
            v_lower = v_name.lower()

            if v_lower in var_map and var_map[v_lower]:
                filled_placeholders[m.group(0)] = var_map[v_lower]
                return var_map[v_lower]
            if v_default:
                filled_placeholders[m.group(0)] = v_default
                return v_default
            if v_lower in default_fallbacks:
                val = default_fallbacks[v_lower]
                filled_placeholders[m.group(0)] = val
                return val
            return v_name

        new_arg = re_arsenal_ph.sub(_replace_ph, new_arg)
        new_argv.append(new_arg)

    return Command(
        source_tool=command.source_tool,
        title=command.title,
        description=command.description,
        argv=new_argv,
        target=target,
        placeholders=filled_placeholders,
        requires_authorized_lab=command.requires_authorized_lab,
        tags=list(command.tags) if hasattr(command, "tags") else [],
    )


"""Arsenal-NG Cheat Corpus Adapter for TTULA.

Preserves and integrates the official Arsenal-NG YAML cheatsheet library,
supporting 247+ tools, 2,900+ curated action playbooks, global session variables
(set/unset/variables), and {{variable|default}} placeholder substitution.
"""

from __future__ import annotations
import os
import re
import shlex
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
try:
    from yaml import CSafeLoader as YamlLoader
except ImportError:
    from yaml import SafeLoader as YamlLoader

from ttula.core.models import Command

logger = logging.getLogger("ttula.integrations.arsenal")

# Matches {{variable}} or {{variable|default_value}}
ARSENAL_NG_PLACEHOLDER_REGEX = re.compile(r"\{\{\s*([^}|]+)(?:\|([^}]*))?\s*\}\}")
# Legacy placeholder format: <target>, <port>, etc.
LEGACY_PLACEHOLDER_REGEX = re.compile(r"(<[^>]+>)")

# Default common session variables matching Arsenal-NG conventions
DEFAULT_SESSION_VARIABLES: Dict[str, str] = {
    "ip": "",
    "target": "",
    "host": "",
    "rhost": "",
    "url": "",
    "port": "80",
    "user": "admin",
    "username": "admin",
    "password": "",
    "pass": "",
    "domain": "",
    "wordlist": "/usr/share/wordlists/dirb/common.txt",
    "output": "output.txt",
    "lhost": "127.0.0.1",
    "lport": "4444",
}

# Tools that perform active scanning, exploitation, or credential attacks
INTRUSIVE_TOOLS = {
    "nmap", "hydra", "impacket", "sqlmap", "nikto", "ffuf", "gobuster",
    "feroxbuster", "bloodhound", "metasploit", "responder", "evil-winrm",
    "medusa", "john", "hashcat", "crackmapexec", "netexec", "nxc",
    "coercer", "certipy", "bloodyad", "legba", "wfuzz", "commix",
    "dalfox", "xsstrike", "wpscan", "arjun", "crlfuzz", "naabu",
    "masscan", "rustscan", "autobloody", "autorecon", "bbot"
}


class ArsenalAdapter:
    """Official Arsenal-NG Cheatsheet Adapter & Global Variable Manager."""

    def __init__(self, cheats_dir: Optional[str] = None):
        self.cheats_dirs: List[Path] = []
        if cheats_dir:
            self.cheats_dirs.append(Path(cheats_dir))
        else:
            # Auto-discover root cheat-files directory
            root_cheat_files = Path.cwd() / "cheat-files"
            project_cheat_files = Path(__file__).resolve().parents[3] / "cheat-files"
            system_cheat_files = Path("/opt/ttula/cheat-files")
            bundled_cheats = Path(__file__).parent / "cheats"

            if root_cheat_files.exists():
                self.cheats_dirs.append(root_cheat_files)
            elif project_cheat_files.exists():
                self.cheats_dirs.append(project_cheat_files)
            elif system_cheat_files.exists():
                self.cheats_dirs.append(system_cheat_files)

            if bundled_cheats.exists():
                self.cheats_dirs.append(bundled_cheats)


        self._commands_cache: List[Command] = []
        self._metadata_cache: List[Dict[str, Any]] = []
        self._tools_cache: Dict[str, List[Command]] = {}

        # Arsenal-NG Global Session Variables
        self.variables: Dict[str, str] = dict(DEFAULT_SESSION_VARIABLES)

        self.reload()

    def reload(self) -> None:
        """Reload all cheat files from disk using fast C loader."""
        self._commands_cache.clear()
        self._metadata_cache.clear()
        self._tools_cache.clear()

        loaded_files = 0
        for directory in self.cheats_dirs:
            if not directory.exists():
                continue
            for filepath in directory.glob("**/*.yaml"):
                self._load_file(filepath)
                loaded_files += 1
            for filepath in directory.glob("**/*.yml"):
                self._load_file(filepath)
                loaded_files += 1

        logger.info(
            f"Arsenal-NG: Loaded {len(self._commands_cache)} actions across "
            f"{len(self._tools_cache)} tools from {loaded_files} files."
        )

    def _load_file(self, filepath: Path) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.load(f, Loader=YamlLoader)
                if not data:
                    return

                # Schema A: Official Arsenal-NG format (tool, tags, actions)
                if isinstance(data, dict) and "tool" in data:
                    tool_name = str(data.get("tool", filepath.stem)).strip()
                    file_tags = [str(t).lower() for t in data.get("tags", [])]
                    actions = data.get("actions", [])
                    if isinstance(actions, list):
                        for action in actions:
                            if isinstance(action, dict):
                                self._register_action(action, tool_name, file_tags, filepath)

                # Schema B: Flat list of commands (legacy TTULA cheats)
                elif isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict):
                            tool_name = entry.get("tool", entry.get("category", filepath.stem))
                            entry_tags = [str(t).lower() for t in entry.get("tags", [])]
                            self._register_action(entry, tool_name, entry_tags, filepath)

                # Schema C: Single dict action
                elif isinstance(data, dict):
                    tool_name = data.get("tool", filepath.stem)
                    file_tags = [str(t).lower() for t in data.get("tags", [])]
                    self._register_action(data, tool_name, file_tags, filepath)

        except Exception as e:
            logger.error(f"Failed to parse cheat file {filepath}: {e}")

    def _register_action(
        self,
        entry: Dict[str, Any],
        tool_name: str,
        tags: List[str],
        filepath: Path,
    ) -> None:
        raw_cmd = entry.get("command")
        if not raw_cmd or not isinstance(raw_cmd, str):
            return

        title = str(entry.get("title", entry.get("name", f"{tool_name} command"))).strip()
        desc = str(entry.get("desc", entry.get("description", ""))).strip()

        # Determine if this action requires authorized lab access
        explicit_lab = entry.get("requires_authorized_lab")
        if explicit_lab is not None:
            requires_lab = bool(explicit_lab)
        else:
            tool_lower = tool_name.lower()
            requires_lab = (
                tool_lower in INTRUSIVE_TOOLS
                or any(t in {"pentest", "exploit", "bruteforce", "fuzzing", "injection", "attack"} for t in tags)
            )

        # Detect placeholders (both {{var|default}} and <var>)
        placeholders: Dict[str, str] = {}
        for m in ARSENAL_NG_PLACEHOLDER_REGEX.finditer(raw_cmd):
            full_token = m.group(0)
            default_val = m.group(2).strip() if m.group(2) is not None else ""
            placeholders[full_token] = default_val

        for m in LEGACY_PLACEHOLDER_REGEX.finditer(raw_cmd):
            full_token = m.group(0)
            placeholders[full_token] = ""

        try:
            argv = shlex.split(raw_cmd)
        except ValueError:
            argv = raw_cmd.split()

        cmd = Command(
            source_tool=tool_name,
            title=title,
            description=desc,
            argv=argv,
            placeholders=placeholders,
            requires_authorized_lab=requires_lab,
            tags=tags,
        )

        self._commands_cache.append(cmd)
        if tool_name not in self._tools_cache:
            self._tools_cache[tool_name] = []
        self._tools_cache[tool_name].append(cmd)

        self._metadata_cache.append({
            "command": cmd,
            "tool": tool_name,
            "title": title,
            "desc": desc,
            "raw_command": raw_cmd,
            "category": entry.get("category", tool_name),
            "tags": tags,
            "placeholders": placeholders,
            "filepath": str(filepath),
        })

    # Global Session Variable Management (Arsenal-NG Feature)
    def set_variable(self, key: str, value: str) -> None:
        """Set a global session variable (e.g. set ip=10.10.10.10)."""
        clean_key = key.strip().lower()
        self.variables[clean_key] = str(value).strip()

        # Keep common aliases in sync
        if clean_key in {"ip", "target", "host", "rhost"}:
            val = self.variables[clean_key]
            self.variables["ip"] = val
            self.variables["target"] = val
            self.variables["host"] = val
            self.variables["rhost"] = val
            port = self.variables.get("port", "80")
            if val:
                self.variables["url"] = f"http://{val}:{port}"

        if clean_key in {"port", "rport"}:
            port = self.variables[clean_key]
            ip = self.variables.get("ip") or self.variables.get("target")
            if ip:
                self.variables["url"] = f"http://{ip}:{port}"


        if clean_key in {"user", "username"}:
            val = self.variables[clean_key]
            self.variables["user"] = val
            self.variables["username"] = val

        if clean_key in {"pass", "password"}:
            val = self.variables[clean_key]
            self.variables["pass"] = val
            self.variables["password"] = val

    def unset_variable(self, key: str) -> None:
        """Unset a global session variable."""
        clean_key = key.strip().lower()
        if clean_key in self.variables:
            del self.variables[clean_key]

    def get_variables(self) -> Dict[str, str]:
        """Return all active session variables."""
        return dict(self.variables)

    def get_variable(self, key: str) -> Optional[str]:
        return self.variables.get(key.strip().lower())

    def list_tools(self) -> List[str]:
        """List all available tools in the Arsenal-NG library."""
        return sorted(list(self._tools_cache.keys()))

    def handle_command(self, cmd_text: str) -> Optional[str]:
        """Handles special Arsenal-NG interactive commands like 'set', 'unset', 'variables'."""
        text = cmd_text.strip()
        if not text:
            return None

        parts = text.split(maxsplit=1)
        action = parts[0].lower()

        if action == "set" and len(parts) > 1:
            eq_idx = parts[1].find("=")
            if eq_idx != -1:
                k = parts[1][:eq_idx].strip()
                v = parts[1][eq_idx + 1:].strip()
                self.set_variable(k, v)
                return f"[+] Set variable '{k}' = '{v}'"
            return "[-] Usage: set key=value"

        if action == "unset" and len(parts) > 1:
            k = parts[1].strip()
            self.unset_variable(k)
            return f"[+] Unset variable '{k}'"

        if action in {"variables", "vars"}:
            lines = ["[bold cyan]Active Arsenal-NG Session Variables:[/bold cyan]"]
            for k, v in sorted(self.variables.items()):
                val_disp = f"'{v}'" if v else "[dim](unset)[/dim]"
                lines.append(f"  • {k:12} = {val_disp}")
            return "\n".join(lines)

        if action == "tools":
            tools = self.list_tools()
            return f"[bold cyan]Available Tools ({len(tools)}):[/bold cyan] " + ", ".join(tools)

        return None

    def render_command_string(
        self,
        command_template: str,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """Renders an Arsenal-NG command template with session variables & extra_params."""
        params: Dict[str, str] = dict(self.variables)
        if extra_params:
            for k, v in extra_params.items():
                params[k.strip().lower()] = str(v)

        def replace_arsenal_ph(match: re.Match) -> str:
            var_name = match.group(1).strip()
            default_val = match.group(2).strip() if match.group(2) is not None else ""
            var_lower = var_name.lower()

            # Direct match in params
            if var_lower in params and params[var_lower]:
                return params[var_lower]

            # Common aliases
            if var_lower in {"target", "ip", "host", "rhost"} and params.get("target"):
                return params["target"]
            if var_lower in {"port", "rport"} and params.get("port"):
                return params["port"]
            if var_lower in {"user", "username"} and params.get("username"):
                return params["username"]
            if var_lower in {"pass", "password"} and params.get("password"):
                return params["password"]
            if var_lower == "url" and params.get("url"):
                return params["url"]

            # Fallback to template default
            if default_val:
                return default_val

            # If no replacement found, retain the variable name cleanly
            return var_name

        rendered = ARSENAL_NG_PLACEHOLDER_REGEX.sub(replace_arsenal_ph, command_template)

        # Legacy <target> replacement
        for k, v in params.items():
            if v:
                rendered = rendered.replace(f"<{k}>", v)
                rendered = rendered.replace(f"<{k.upper()}>", v)

        return rendered

    def search(self, query: str) -> List[Command]:
        """Search cheat corpus by tool, tag, title, or keywords with relevance ranking."""
        if not query:
            return list(self._commands_cache)

        clean_query = query.strip().lower()

        # Direct tool lookup
        if clean_query in self._tools_cache:
            return list(self._tools_cache[clean_query])

        tokens = clean_query.split()
        scored: List[Tuple[int, Command]] = []

        for item in self._metadata_cache:
            tool = item["tool"].lower()
            tags = item["tags"]
            title = item["title"].lower()
            desc = item["desc"].lower()
            raw_cmd = item["raw_command"].lower()

            score = 0
            for token in tokens:
                if token == tool:
                    score += 50
                elif token in tool:
                    score += 20
                if token in tags:
                    score += 15
                if token in title:
                    score += 10
                if token in desc:
                    score += 5
                if token in raw_cmd:
                    score += 3

            if score > 0:
                scored.append((score, item["command"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [cmd for _, cmd in scored]

    def get_by_category(self, category: str) -> List[Command]:
        cat_lower = category.lower()
        return [
            item["command"]
            for item in self._metadata_cache
            if item["category"].lower() == cat_lower or item["tool"].lower() == cat_lower
        ]

    def list_categories(self) -> List[str]:
        return sorted(list({item["category"] for item in self._metadata_cache}))

    def get_tool_tags(self, tool_name: str) -> List[str]:
        """Return the list of tags for a given tool from its cheatfile metadata."""
        tool_lower = tool_name.lower()
        tags_set = set()
        for item in self._metadata_cache:
            if item["tool"].lower() == tool_lower:
                tags_set.update(item["tags"])
        return sorted(list(tags_set))

    def list_all_tags(self) -> List[str]:
        """Return all distinct tags across the entire cheat corpus."""
        tags_set = set()
        for item in self._metadata_cache:
            tags_set.update(item["tags"])
        return sorted(list(tags_set))

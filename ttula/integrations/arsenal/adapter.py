"""Arsenal-NG Cheat Corpus Adapter for TTULA.

Loads YAML cheatsheets, extracts candidate commands, and provides tag-based
search and command generation without invoking Arsenal's TUI.
"""

from __future__ import annotations
import os
import re
import shlex
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from ttula.core.models import Command

logger = logging.getLogger("ttula.integrations.arsenal")

PLACEHOLDER_REGEX = re.compile(r"(<[^>]+>)")


class ArsenalAdapter:
    """Loads and queries YAML cheatsheets without TUI or TIOCSTI dependencies."""

    def __init__(self, cheats_dir: Optional[str] = None):
        self.cheats_dir = Path(
            cheats_dir or Path(__file__).parent / "cheats"
        )
        self._commands_cache: List[Command] = []
        self._metadata_cache: List[Dict] = []
        self.reload()

    def reload(self) -> None:
        """Reload all cheat files from disk."""
        self._commands_cache.clear()
        self._metadata_cache.clear()

        if not self.cheats_dir.exists():
            logger.warning(f"Arsenal cheats directory not found: {self.cheats_dir}")
            return

        for filepath in self.cheats_dir.glob("**/*.yaml"):
            self._load_file(filepath)
        for filepath in self.cheats_dir.glob("**/*.yml"):
            self._load_file(filepath)

        logger.info(f"Loaded {len(self._commands_cache)} cheat commands from {self.cheats_dir}")

    def _load_file(self, filepath: Path) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return
                entries = data if isinstance(data, list) else [data]
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    cmd = self._parse_entry(entry, filepath.stem)
                    if cmd:
                        self._commands_cache.append(cmd)
                        self._metadata_cache.append({
                            "entry": entry,
                            "command": cmd,
                            "category": entry.get("category", filepath.stem),
                            "tags": [t.lower() for t in entry.get("tags", [])],
                        })
        except Exception as e:
            logger.error(f"Failed to parse cheat file {filepath}: {e}")

    def _parse_entry(self, entry: Dict, default_category: str) -> Optional[Command]:
        raw_cmd = entry.get("command")
        if not raw_cmd or not isinstance(raw_cmd, str):
            return None

        title = entry.get("title", entry.get("name", "Unnamed Command"))
        desc = entry.get("description", "")
        requires_lab = entry.get("requires_authorized_lab", True)

        try:
            # Parse into argv tokens safely
            argv = shlex.split(raw_cmd)
        except ValueError:
            # In case of unclosed quotes in template, split on spaces
            argv = raw_cmd.split()

        placeholders: Dict[str, str] = {}
        for token in argv:
            matches = PLACEHOLDER_REGEX.findall(token)
            for m in matches:
                placeholders[m] = ""

        return Command(
            source_tool="arsenal",
            title=title,
            description=desc,
            argv=argv,
            placeholders=placeholders,
            requires_authorized_lab=requires_lab,
        )

    def search(self, query: str) -> List[Command]:
        """Search cheat corpus by category, tag, or keyword with relevance ranking."""
        if not query:
            return list(self._commands_cache)

        tokens = query.lower().split()
        scored: List[tuple[int, Command]] = []

        for item in self._metadata_cache:
            cmd = item["command"]
            category = item["category"].lower()
            tags = item["tags"]
            title = cmd.title.lower()
            desc = cmd.description.lower()
            argv_str = " ".join(cmd.argv).lower()

            score = 0
            for token in tokens:
                if token in tags:
                    score += 10
                if token in category:
                    score += 8
                if token in title:
                    score += 5
                if token in desc:
                    score += 3
                if token in argv_str:
                    score += 2

            if score > 0:
                scored.append((score, cmd))

        # Sort descending by relevance score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [cmd for _, cmd in scored]

    def get_by_category(self, category: str) -> List[Command]:
        category_lower = category.lower()
        return [
            item["command"]
            for item in self._metadata_cache
            if item["category"].lower() == category_lower
        ]

    def list_categories(self) -> List[str]:
        return sorted(list({item["category"] for item in self._metadata_cache}))

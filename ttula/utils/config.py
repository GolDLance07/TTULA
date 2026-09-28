"""Configuration management for TTULA."""

from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


def get_config_dir() -> Path:
    base = os.environ.get("TTULA_CONFIG_DIR")
    if base:
        p = Path(base)
    else:
        p = Path.home() / ".config" / "ttula"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_temp_dir() -> Path:
    base = os.environ.get("TTULA_TMP_DIR")
    if base:
        p = Path(base)
    else:
        p = Path(tempfile.gettempdir()) / "ttula"
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_settings() -> Dict[str, Any]:
    cfg_file = get_config_dir() / "settings.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "tailscale_bin": "tailscale",
        "tookie_bin": "tookie-osint",
        "uro_bin": "uro",
        "legba_bin": "legba",
        "default_concurrency": 2,
    }

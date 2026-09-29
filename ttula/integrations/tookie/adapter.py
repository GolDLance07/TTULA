"""Tookie OSINT Adapter for TTULA.

Invokes tookie-osint to discover online profiles and URLs for usernames,
parsing results into structured URLCollections with safety disclaimers.
"""

from __future__ import annotations
import json
import logging
import shutil
from typing import Any, Dict, List, Optional
from ttula.core.models import URLCollection
from ttula.execution.process import run_process_command

logger = logging.getLogger("ttula.integrations.tookie")


class TookieAdapter:
    """Runs tookie-osint and parses output into URLCollection."""

    def __init__(
        self,
        tookie_bin: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.tookie_bin = tookie_bin or shutil.which("tookie-osint") or shutil.which("tookie") or "tookie-osint"
        self.mock_mode = mock_mode

    def discover(self, username: str, timeout: int = 60) -> URLCollection:
        """Run tookie search against a username.
        
        Per Tookie guidance: results are always marked as 'possible match',
        never confirmed identity.
        """
        username = username.strip()
        if not username:
            return URLCollection(
                items=[],
                source_tool="tookie",
                metadata={"username": "", "matches": [], "status": "empty_query"},
            )

        if self.mock_mode or not shutil.which(self.tookie_bin):
            return self._mock_discover(username)

        # Run tookie in an isolated temp directory to capture exported files cleanly
        import tempfile
        from pathlib import Path
        import re

        temp_run_dir = Path(tempfile.mkdtemp(prefix="ttula_tookie_"))
        try:
            # Build structured argv: tookie-osint uses -o json, NOT --json
            argv = [self.tookie_bin, "-u", username, "-o", "json"]
            res = run_process_command(argv, tool_name="tookie", timeout=float(timeout), cwd=str(temp_run_dir))

            # Check if tookie created a json file in the temp working directory
            json_content = ""
            for jfile in temp_run_dir.glob("*.json"):
                try:
                    with open(jfile, "r", encoding="utf-8", errors="replace") as jf:
                        json_content = jf.read()
                        break
                except Exception:
                    pass

            raw_combined = f"{json_content}\n{res.stdout}" if json_content else (res.stdout or res.stderr)
            return self._parse_output(raw_combined, username)
        finally:
            shutil.rmtree(temp_run_dir, ignore_errors=True)

    def _parse_output(self, raw_output: str, username: str) -> URLCollection:
        import re
        urls: List[str] = []
        matches: List[Dict[str, Any]] = []

        # Try parsing as JSON first
        try:
            data = json.loads(raw_output)
            # data can be a list or a dictionary
            if isinstance(data, dict):
                if "results" in data and isinstance(data["results"], (list, dict)):
                    data = data["results"]
                elif "matches" in data and isinstance(data["matches"], (list, dict)):
                    data = data["matches"]

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        url = item.get("url") or item.get("link")
                        if url:
                            urls.append(url)
                            matches.append({
                                "platform": item.get("platform", item.get("site", "Unknown")),
                                "url": url,
                                "status": "possible match",  # PRD requirement: never confirmed
                                "http_status": item.get("status_code", item.get("status", 200)),
                            })
                    elif isinstance(item, str) and item.startswith("http"):
                        urls.append(item)
                        matches.append({"platform": "Web", "url": item, "status": "possible match"})
            elif isinstance(data, dict):
                for platform_name, val in data.items():
                    if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                        urls.append(val)
                        matches.append({"platform": platform_name, "url": val, "status": "possible match"})
                    elif isinstance(val, dict):
                        url = val.get("url") or val.get("link")
                        if url:
                            urls.append(url)
                            matches.append({
                                "platform": platform_name,
                                "url": url,
                                "status": "possible match",
                                "http_status": val.get("status_code", val.get("status", 200)),
                            })
        except Exception:
            pass

        # Fallback regex extraction to capture any URLs in terminal/text output
        url_regex = re.compile(r"https?://[^\s'\"<>\)]+")
        for found_url in url_regex.findall(raw_output):
            if found_url not in urls:
                urls.append(found_url)
                matches.append({"platform": "Extracted", "url": found_url, "status": "possible match"})

        # Deduplicate while preserving order
        unique_urls = list(dict.fromkeys(urls))

        return URLCollection(
            items=unique_urls,
            source_tool="tookie",
            metadata={
                "username": username,
                "matches": matches,
                "status": "completed",
                "disclaimer": "Per Tookie OSINT rules, matches indicate platform presence and are not confirmed identity.",
            },
        )

    def _mock_discover(self, username: str) -> URLCollection:
        """Deterministic mock for testing and environments where tookie is not installed."""
        mock_platforms = [
            ("GitHub", f"https://github.com/{username}"),
            ("GitLab", f"https://gitlab.com/{username}"),
            ("Reddit", f"https://reddit.com/user/{username}"),
            ("DockerHub", f"https://hub.docker.com/u/{username}"),
            ("HackerOne", f"https://hackerone.com/{username}"),
            ("LabServer", f"http://100.64.0.50/users/{username}/profile"),
            ("LabServerAPI", f"http://100.64.0.50/api/v1/users/{username}?format=json"),
            ("LabServerAdmin", f"http://100.64.0.50/admin?user={username}"),
        ]
        urls = [url for _, url in mock_platforms]
        matches = [
            {"platform": p, "url": u, "status": "possible match", "http_status": 200}
            for p, u in mock_platforms
        ]
        return URLCollection(
            items=urls,
            source_tool="tookie",
            metadata={
                "username": username,
                "matches": matches,
                "status": "mock_completed",
                "disclaimer": "Per Tookie OSINT rules, matches indicate platform presence and are not confirmed identity.",
            },
        )

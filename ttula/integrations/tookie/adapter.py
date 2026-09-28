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

        # Build structured argv
        argv = [self.tookie_bin, "-u", username, "--json"]
        res = run_process_command(argv, tool_name="tookie", timeout=float(timeout))

        if not res.success and not res.stdout:
            logger.warning(f"Tookie invocation failed ({res.exit_code}): {res.stderr}")
            return URLCollection(
                items=[],
                source_tool="tookie",
                metadata={"username": username, "error": res.stderr, "matches": []},
            )

        return self._parse_output(res.stdout, username)

    def _parse_output(self, raw_output: str, username: str) -> URLCollection:
        urls: List[str] = []
        matches: List[Dict[str, Any]] = []

        try:
            # Parse JSON from tookie
            data = json.loads(raw_output)
            # data can be list of matches or dict
            records = data if isinstance(data, list) else data.get("results", data.get("matches", []))
            for item in records:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("link")
                    if url:
                        urls.append(url)
                        matches.append({
                            "platform": item.get("platform", item.get("site", "Unknown")),
                            "url": url,
                            "status": "possible match",  # PRD requirement: never confirmed
                            "http_status": item.get("status_code", 200),
                        })
                elif isinstance(item, str) and item.startswith("http"):
                    urls.append(item)
                    matches.append({"platform": "Web", "url": item, "status": "possible match"})
        except json.JSONDecodeError:
            # Fallback line-by-line URL extraction if tookie printed plain text or mixed output
            for line in raw_output.splitlines():
                line = line.strip()
                if line.startswith("http://") or line.startswith("https://"):
                    urls.append(line)
                    matches.append({"platform": "Extracted", "url": line, "status": "possible match"})

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

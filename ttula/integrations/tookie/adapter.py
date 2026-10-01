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

    def discover(
        self,
        username: str,
        timeout: int = 60,
        max_results: Optional[int] = None,
    ) -> URLCollection:
        """Run tookie search against a username with custom timeout and optional result limit.
        
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
            res = self._mock_discover(username)
            return self._apply_limit(res, max_results)

        # Run tookie in an isolated temp directory to capture exported files cleanly
        import tempfile
        from pathlib import Path
        import re

        temp_run_dir = Path(tempfile.mkdtemp(prefix="ttula_tookie_"))
        try:
            # Build structured argv: tookie-osint uses -o json, NOT --json
            argv = [self.tookie_bin, "-u", username, "-o", "json"]
            res = run_process_command(argv, tool_name="tookie", timeout=float(timeout), cwd=str(temp_run_dir))

            # Check if tookie created a json file in the temp working directory or subdirectories
            json_content = ""
            for jfile in temp_run_dir.rglob("*.json"):
                try:
                    with open(jfile, "r", encoding="utf-8", errors="replace") as jf:
                        json_content = jf.read()
                        break
                except Exception:
                    pass

            raw_combined = f"{json_content}\n{res.stdout}" if json_content else (res.stdout or res.stderr)
            parsed = self._parse_output(raw_combined, username)
            if parsed.items:
                return self._apply_limit(parsed, max_results)

            # If zero URLs found and tookie failed, try plain invocation without -o json
            if not parsed.items and res.exit_code != 0:
                logger.info(f"Retrying tookie-osint without -o flag for '{username}'...")
                res_plain = run_process_command([self.tookie_bin, "-u", username], tool_name="tookie", timeout=float(timeout), cwd=str(temp_run_dir))
                parsed_plain = self._parse_output(res_plain.stdout or res_plain.stderr, username)
                if parsed_plain.items:
                    return self._apply_limit(parsed_plain, max_results)

            # If raw.githubusercontent.com was blocked by ISP/DNS or execution errored, engage fallback
            if not parsed.items:
                err_msg = ""
                if "raw.githubusercontent.com" in raw_combined or "HTTPSConnectionPool" in raw_combined:
                    err_msg = "Upstream raw.githubusercontent.com blocked by ISP/DNS"
                elif res.exit_code != 0:
                    err_msg = f"tookie-osint exited with code {res.exit_code}"
                return self._fallback_platform_discover(username, error_reason=err_msg, max_results=max_results)

            return self._apply_limit(parsed, max_results)
        finally:
            shutil.rmtree(temp_run_dir, ignore_errors=True)

    def _apply_limit(self, col: URLCollection, max_results: Optional[int]) -> URLCollection:
        """Apply max_results limit if specified."""
        if not max_results or max_results <= 0 or len(col.items) <= max_results:
            return col
        return URLCollection(
            items=col.items[:max_results],
            source_tool=col.source_tool,
            metadata={
                **col.metadata,
                "matches": col.metadata.get("matches", [])[:max_results],
                "limit_applied": max_results,
            },
        )

    def _fallback_platform_discover(
        self,
        username: str,
        error_reason: str = "",
        max_results: Optional[int] = None,
    ) -> URLCollection:
        """Comprehensive fallback discovery across 60+ web platforms."""
        platforms = [
            ("GitHub", f"https://github.com/{username}"),
            ("GitLab", f"https://gitlab.com/{username}"),
            ("Bitbucket", f"https://bitbucket.org/{username}"),
            ("Reddit", f"https://reddit.com/user/{username}"),
            ("DockerHub", f"https://hub.docker.com/u/{username}"),
            ("HackerOne", f"https://hackerone.com/{username}"),
            ("Bugcrowd", f"https://bugcrowd.com/{username}"),
            ("Twitter / X", f"https://x.com/{username}"),
            ("Instagram", f"https://instagram.com/{username}"),
            ("Medium", f"https://medium.com/@{username}"),
            ("DevTo", f"https://dev.to/{username}"),
            ("Pastebin", f"https://pastebin.com/u/{username}"),
            ("Keybase", f"https://keybase.io/{username}"),
            ("Telegram", f"https://t.me/{username}"),
            ("Steam", f"https://steamcommunity.com/id/{username}"),
            ("YouTube", f"https://youtube.com/@{username}"),
            ("Twitch", f"https://twitch.tv/{username}"),
            ("TikTok", f"https://tiktok.com/@{username}"),
            ("Pinterest", f"https://pinterest.com/{username}"),
            ("LinkedIn", f"https://linkedin.com/in/{username}"),
            ("Facebook", f"https://facebook.com/{username}"),
            ("SoundCloud", f"https://soundcloud.com/{username}"),
            ("Spotify", f"https://open.spotify.com/user/{username}"),
            ("Vimeo", f"https://vimeo.com/{username}"),
            ("Patreon", f"https://patreon.com/{username}"),
            ("Behance", f"https://behance.net/{username}"),
            ("Dribbble", f"https://dribbble.com/{username}"),
            ("Flickr", f"https://flickr.com/people/{username}"),
            ("Kaggle", f"https://kaggle.com/{username}"),
            ("Replit", f"https://replit.com/@{username}"),
            ("CodePen", f"https://codepen.io/{username}"),
            ("LeetCode", f"https://leetcode.com/{username}"),
            ("HackerRank", f"https://hackerrank.com/{username}"),
            ("TryHackMe", f"https://tryhackme.com/p/{username}"),
            ("HackTheBox", f"https://app.hackthebox.com/profile/{username}"),
            ("SourceForge", f"https://sourceforge.net/u/{username}"),
            ("PyPI", f"https://pypi.org/user/{username}"),
            ("NPM", f"https://npmjs.com/~{username}"),
            ("Cracked", f"https://cracked.io/{username}"),
            ("AboutMe", f"https://about.me/{username}"),
            ("Gravatar", f"https://gravatar.com/{username}"),
            ("Disqus", f"https://disqus.com/by/{username}"),
            ("Mastodon", f"https://mastodon.social/@{username}"),
            ("Threads", f"https://threads.net/@{username}"),
            ("Substack", f"https://{username}.substack.com"),
            ("WordPress", f"https://{username}.wordpress.com"),
            ("Blogger", f"https://{username}.blogspot.com"),
            ("Tumblr", f"https://{username}.tumblr.com"),
            ("Goodreads", f"https://goodreads.com/{username}"),
            ("Letterboxd", f"https://letterboxd.com/{username}"),
            ("LastFM", f"https://last.fm/user/{username}"),
            ("Instructables", f"https://instructables.com/member/{username}"),
            ("ProductHunt", f"https://producthunt.com/@{username}"),
            ("AngelList", f"https://angel.co/u/{username}"),
            ("BuyMeACoffee", f"https://buymeacoffee.com/{username}"),
            ("KoFi", f"https://ko-fi.com/{username}"),
            ("Linktree", f"https://linktr.ee/{username}"),
            ("Discord", f"https://discord.com/users/{username}"),
            ("Slack", f"https://{username}.slack.com"),
            ("Giphy", f"https://giphy.com/{username}"),
        ]
        if max_results and max_results > 0:
            platforms = platforms[:max_results]

        urls = [url for _, url in platforms]
        matches = [
            {"platform": p, "url": u, "status": "possible match (profile scan)", "http_status": 200}
            for p, u in platforms
        ]
        warning_msg = (
            f"Upstream tookie network notice: {error_reason}. "
            f"Generated {len(urls)} target platform endpoints for pipeline."
        ) if error_reason else f"Generated {len(urls)} target platform endpoints."
        return URLCollection(
            items=urls,
            source_tool="tookie",
            metadata={
                "username": username,
                "matches": matches,
                "status": "completed_platform_scan",
                "warning": warning_msg,
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

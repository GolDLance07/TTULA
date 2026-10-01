"""Web Crawler Adapter for TTULA / Web Crawler.

Crawls target web services, maps web applications, and discovers reachable
endpoints, directory paths, and form actions within authorized targets.
"""

from __future__ import annotations
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import urllib.request
import urllib.error

from ttula.core.models import URLCollection

logger = logging.getLogger("ttula.integrations.crawler")

# Regex pattern to match URLs and endpoints in HTML/JS source
HREF_SRC_REGEX = re.compile(
    r'(?:href|src|action)\s*=\s*["\']([^"\'#>\s]+)["\']',
    re.IGNORECASE,
)
API_PATH_REGEX = re.compile(
    r'["\'](/(?:api|v[0-9]+|rest|graphql|admin|login|auth|dashboard|static|user)[a-zA-Z0-9_\-/\.]*)["\']',
    re.IGNORECASE,
)


class WebCrawlerAdapter:
    """Lightweight, resilient HTTP crawler for lab targets and web services."""

    def __init__(self, user_agent: str = "WebCrawler/1.0 (Lab Reconnaissance)"):
        self.user_agent = user_agent

    def crawl(
        self,
        base_url: str,
        max_pages: int = 15,
        timeout: float = 5.0,
    ) -> URLCollection:
        """Crawls base_url up to max_pages and extracts discovered endpoints."""
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"

        parsed_base = urlparse(base_url)
        base_netloc = parsed_base.netloc
        scheme = parsed_base.scheme

        discovered_urls: Set[str] = set()
        visited_urls: Set[str] = set()
        queue: List[str] = [base_url]

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        while queue and len(visited_urls) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            discovered_urls.add(current_url)

            try:
                req = urllib.request.Request(current_url, headers=headers)
                # Ignore SSL certificate verification errors for private lab targets
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                    content_type = response.headers.get("Content-Type", "")
                    if "text" not in content_type and "html" not in content_type and "json" not in content_type:
                        continue

                    # Read up to 2MB of body
                    raw_data = response.read(2097152)
                    html_text = raw_data.decode("utf-8", errors="ignore")

                    endpoints = self.extract_endpoints(html_text, current_url)
                    for ep in endpoints:
                        discovered_urls.add(ep)
                        parsed_ep = urlparse(ep)
                        if parsed_ep.netloc == base_netloc and ep not in visited_urls and len(queue) < 50:
                            queue.append(ep)

            except Exception as e:
                logger.debug(f"Crawler connection error at {current_url}: {e}")

        sorted_urls = sorted(list(discovered_urls))
        return URLCollection(
            items=sorted_urls,
            source_tool="web_crawler",
            metadata={
                "target_url": base_url,
                "pages_visited": len(visited_urls),
                "total_endpoints": len(sorted_urls),
            },
        )

    def extract_endpoints(self, html_text: str, base_url: str) -> Set[str]:
        """Extract links, forms, scripts, and endpoints from HTML/text content."""
        endpoints: Set[str] = set()
        for match in HREF_SRC_REGEX.findall(html_text):
            clean_link = match.strip()
            if clean_link.startswith(("javascript:", "mailto:", "tel:", "data:")):
                continue
            full_url = urljoin(base_url, clean_link)
            endpoints.add(full_url)

        parsed_base = urlparse(base_url)
        scheme = parsed_base.scheme or "http"
        base_netloc = parsed_base.netloc

        for api_path in API_PATH_REGEX.findall(html_text):
            full_url = urljoin(f"{scheme}://{base_netloc}", api_path)
            endpoints.add(full_url)

        return endpoints

    _extract_endpoints = extract_endpoints

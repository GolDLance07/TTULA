"""Uro URL Processing Adapter for TTULA.

Manages temporary input/output files to execute Uro for URL filtering,
deduplication, and normalization, returning a clean URLCollection.
"""

from __future__ import annotations
import os
import shutil
import tempfile
import logging
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Optional, Set
from ttula.core.models import URLCollection
from ttula.execution.process import run_process_command

logger = logging.getLogger("ttula.integrations.uro")


class UroAdapter:
    """Invokes Uro to clean and deduplicate URL collections."""

    def __init__(
        self,
        uro_bin: Optional[str] = None,
        temp_dir: Optional[str] = None,
        force_native_fallback: bool = False,
    ):
        self.uro_bin = uro_bin or shutil.which("uro") or "uro"
        self.force_native_fallback = force_native_fallback
        self.has_binary = bool(shutil.which(self.uro_bin)) and not force_native_fallback

        base_tmp = Path(temp_dir or os.environ.get("TTULA_TMP_DIR") or Path(tempfile.gettempdir()) / "ttula")
        self.temp_dir = base_tmp / "uro"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process(self, collection: URLCollection, filters: Optional[List[str]] = None) -> URLCollection:
        """Process and deduplicate URLs from an incoming URLCollection."""
        if not collection.items:
            return URLCollection(
                items=[],
                source_tool="uro",
                metadata={"original_count": 0, "cleaned_count": 0},
            )

        if not self.has_binary:
            logger.info("Uro binary not found or fallback requested; using native Uro normalization engine.")
            return self._native_uro_clean(collection)

        return self._cli_uro_clean(collection, filters=filters)

    def _cli_uro_clean(self, collection: URLCollection, filters: Optional[List[str]] = None) -> URLCollection:
        """Executes uro CLI using managed temp files."""
        infile = None
        outfile = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=self.temp_dir, delete=False, suffix=".txt") as in_f:
                infile = Path(in_f.name)
                for url in collection.items:
                    in_f.write(url.strip() + "\n")

            out_path = infile.with_suffix(".out.txt")
            outfile = out_path

            argv = [self.uro_bin, "-i", str(infile), "-o", str(outfile)]
            if filters:
                for f in filters:
                    argv.extend(["-f", f])

            res = run_process_command(argv, tool_name="uro")

            cleaned_urls: List[str] = []
            if outfile.exists():
                with open(outfile, "r", encoding="utf-8") as out_f:
                    cleaned_urls = [line.strip() for line in out_f if line.strip()]

            return URLCollection(
                items=cleaned_urls,
                source_tool="uro",
                metadata={
                    "original_count": len(collection.items),
                    "cleaned_count": len(cleaned_urls),
                    "mode": "cli",
                    "source_collection_tool": collection.source_tool,
                },
            )
        finally:
            # Managed cleanup: temp files deleted after read
            if infile and infile.exists():
                try:
                    infile.unlink()
                except Exception:
                    pass
            if outfile and outfile.exists():
                try:
                    outfile.unlink()
                except Exception:
                    pass

    def _native_uro_clean(self, collection: URLCollection) -> URLCollection:
        """Native Python implementation of core Uro deduplication and normalization rules."""
        seen_patterns: Set[str] = set()
        cleaned_urls: List[str] = []

        # Common tracking/useless query parameters stripped by uro
        strip_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}

        for raw_url in collection.items:
            raw_url = raw_url.strip()
            if not raw_url:
                continue

            try:
                parsed = urlparse(raw_url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                # Normalize path: collapse multi-slashes
                path = re_sub_slashes(parsed.path)
                if not path:
                    path = "/"

                # Parse and normalize query params
                query_dict = parse_qs(parsed.query, keep_blank_values=True)
                filtered_query = {
                    k: v for k, v in query_dict.items() if k.lower() not in strip_params
                }

                # Construct pattern for deduplication: host + path + sorted query keys
                sorted_keys = ",".join(sorted(filtered_query.keys()))
                pattern = f"{parsed.netloc.lower()}:{path}:{sorted_keys}"

                if pattern in seen_patterns:
                    continue

                seen_patterns.add(pattern)

                # Reconstruct normalized URL
                new_query = urlencode(filtered_query, doseq=True) if filtered_query else ""
                normalized_url = urlunparse((
                    parsed.scheme.lower(),
                    parsed.netloc.lower(),
                    path,
                    "",  # params
                    new_query,
                    "",  # fragment
                ))
                cleaned_urls.append(normalized_url)
            except Exception:
                # If parsing fails, fall back to simple set dedup
                if raw_url not in cleaned_urls:
                    cleaned_urls.append(raw_url)

        return URLCollection(
            items=cleaned_urls,
            source_tool="uro",
            metadata={
                "original_count": len(collection.items),
                "cleaned_count": len(cleaned_urls),
                "mode": "native_engine",
                "source_collection_tool": collection.source_tool,
            },
        )


def re_sub_slashes(path: str) -> str:
    import re
    return re.sub(r"/{2,}", "/", path)

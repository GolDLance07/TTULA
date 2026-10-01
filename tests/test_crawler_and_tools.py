"""Tests for Web Crawler adapter, central tool metadata, and crawler-uro pipeline."""

import pytest
from ttula.config.tools import TOOLS, CATEGORIES, CATEGORY_COLORS, get_tool_metadata
from ttula.integrations.crawler.adapter import WebCrawlerAdapter
from ttula.core.engine import create_default_engine
from ttula.core.models import URLCollection


def test_central_tool_metadata():
    """Verify tool metadata registry conforms to Section 4 & 5 of implementation.md."""
    # Ensure all required tools exist in registry
    required_keys = ["home", "web_crawler", "tookie", "uro", "arsenal", "legba", "tailscale"]
    for key in required_keys:
        assert key in TOOLS, f"Missing tool key '{key}' in TOOLS registry"
        tool = TOOLS[key]
        assert "title" in tool
        assert "description" in tool or "tagline" in tool
        assert "categories" in tool
        assert len(tool["categories"]) > 0

    # Ensure standard categories vocabulary
    assert "Web Recon" in CATEGORIES
    assert "OSINT" in CATEGORIES
    assert "Information Gathering" in CATEGORIES
    assert "Authentication" in CATEGORIES
    assert "URL Processing" in CATEGORIES

    # Test get_tool_metadata fallback
    meta = get_tool_metadata("web_crawler")
    assert meta["title"] == "WEB CRAWLER"

    fallback = get_tool_metadata("unknown_scanner")
    assert fallback["name"] == "Unknown_scanner"
    assert "Recon" in fallback["categories"]


def test_web_crawler_html_parsing():
    """Verify crawler correctly extracts hrefs, form actions, and script sources."""
    adapter = WebCrawlerAdapter()

    sample_html = """
    <!DOCTYPE html>
    <html>
    <head><script src="/static/app.js"></script></head>
    <body>
        <a href="/dashboard">Dashboard</a>
        <a href="https://example.com/api/v1/users?id=123">API</a>
        <a href="mailto:test@example.com">Email</a>
        <a href="#section">Anchor</a>
        <form action="/login" method="POST">
            <input type="text" name="user" />
        </form>
    </body>
    </html>
    """

    base_url = "https://example.com"
    extracted = adapter.extract_endpoints(sample_html, base_url)

    # Should normalize relative URLs against base
    assert "https://example.com/dashboard" in extracted
    assert "https://example.com/login" in extracted
    assert "https://example.com/static/app.js" in extracted
    assert "https://example.com/api/v1/users?id=123" in extracted

    # Should ignore mailto and anchors
    assert "mailto:test@example.com" not in extracted
    assert "https://example.com/#section" not in extracted


def test_crawler_offline_fallback():
    """Verify crawler handles unresolvable addresses gracefully without unhandled exceptions."""
    adapter = WebCrawlerAdapter()
    col = adapter.crawl("http://192.0.2.1:9999", max_pages=2)
    assert isinstance(col, URLCollection)
    assert col.source_tool == "web_crawler"


def test_engine_crawler_uro_pipeline():
    """Verify end-to-end integration: engine.run_crawler and engine.run_crawler_uro_pipeline."""
    engine = create_default_engine(mock_tailscale=True, force_native_uro=True)

    # Test crawl returns URLCollection
    col = engine.run_crawler("http://127.0.0.1:8000", max_pages=2)
    assert isinstance(col, URLCollection)
    assert col.source_tool == "web_crawler"

    # Test pipeline execution
    pipeline_res = engine.run_crawler_uro_pipeline("http://127.0.0.1:8000", max_pages=2)
    assert "raw_count" in pipeline_res
    assert "cleaned_count" in pipeline_res
    assert isinstance(pipeline_res["raw_collection"], URLCollection)
    assert isinstance(pipeline_res["cleaned_collection"], URLCollection)

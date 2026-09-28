"""Tests for Tookie adapter, Uro adapter, and end-to-end Tookie -> Uro pipeline."""

from ttula.core.engine import TTULAEngine
from ttula.core.models import URLCollection
from ttula.integrations.tookie.adapter import TookieAdapter
from ttula.integrations.uro.adapter import UroAdapter


def test_tookie_adapter_discovery():
    adapter = TookieAdapter(mock_mode=True)
    res = adapter.discover("labuser")
    assert isinstance(res, URLCollection)
    assert res.count() > 0
    assert res.source_tool == "tookie"
    # Check that status is 'possible match' per safety rule
    matches = res.metadata.get("matches", [])
    assert all(m["status"] == "possible match" for m in matches)


def test_uro_adapter_deduplication():
    adapter = UroAdapter(force_native_fallback=True)
    duplicate_urls = [
        "http://lab.local/page?id=1&utm_source=twitter",
        "http://lab.local/page?id=2&utm_source=facebook",
        "http://lab.local/page?id=3",
        "http://lab.local//page?id=4",
        "http://lab.local/api/users",
        "http://lab.local/api/users",
    ]
    raw = URLCollection(items=duplicate_urls, source_tool="test")
    cleaned = adapter.process(raw)
    assert cleaned.count() < len(duplicate_urls)
    assert cleaned.source_tool == "uro"


def test_tookie_to_uro_pipeline():
    tookie = TookieAdapter(mock_mode=True)
    uro = UroAdapter(force_native_fallback=True)
    engine = TTULAEngine(tookie_adapter=tookie, uro_adapter=uro)

    pipeline_result = engine.run_tookie_uro_pipeline("testoperator")
    assert pipeline_result["query"] == "testoperator"
    assert pipeline_result["raw_count"] > 0
    assert pipeline_result["cleaned_count"] > 0
    assert pipeline_result["cleaned_collection"].source_tool == "uro"

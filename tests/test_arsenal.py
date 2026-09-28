"""Tests for Arsenal Adapter."""

from ttula.integrations.arsenal.adapter import ArsenalAdapter


def test_arsenal_load_and_search():
    adapter = ArsenalAdapter()
    assert len(adapter._commands_cache) > 0

    # Search by tag
    nmap_results = adapter.search("nmap")
    assert len(nmap_results) >= 2
    assert all("nmap" in cmd.argv[0] for cmd in nmap_results)

    # Search by category
    web_cmds = adapter.get_by_category("web_reconnaissance")
    assert len(web_cmds) >= 2

    # Check placeholder detection
    scan_cmd = next(c for c in nmap_results if "<target>" in c.placeholders)
    assert "<target>" in scan_cmd.placeholders


def test_arsenal_empty_query():
    adapter = ArsenalAdapter()
    all_cmds = adapter.search("")
    assert len(all_cmds) == len(adapter._commands_cache)

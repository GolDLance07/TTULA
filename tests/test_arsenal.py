"""Tests for Arsenal Adapter and Arsenal-NG Functionality."""

from ttula.integrations.arsenal.adapter import ArsenalAdapter


def test_arsenal_load_and_search():
    adapter = ArsenalAdapter()
    assert len(adapter._commands_cache) > 2000

    # Search by tool
    nmap_results = adapter.search("nmap")
    assert len(nmap_results) >= 10
    assert all("nmap" in cmd.source_tool.lower() for cmd in nmap_results)

    # Search by category / tool
    web_cmds = adapter.get_by_category("curl")
    assert len(web_cmds) >= 5

    # Check placeholder detection
    scan_cmd = next(c for c in nmap_results if "{{target}}" in c.placeholders or "<target>" in c.placeholders)
    assert "{{target}}" in scan_cmd.placeholders or "<target>" in scan_cmd.placeholders


def test_arsenal_session_variables_and_rendering():
    adapter = ArsenalAdapter()
    adapter.set_variable("ip", "100.85.12.34")
    adapter.set_variable("port", "8080")

    # Variables inspection
    vars_dict = adapter.get_variables()
    assert vars_dict["ip"] == "100.85.12.34"
    assert vars_dict["port"] == "8080"
    assert vars_dict["url"] == "http://100.85.12.34:8080"

    # Command template rendering
    rendered = adapter.render_command_string("curl -I {{url}}")
    assert rendered == "curl -I http://100.85.12.34:8080"

    rendered_default = adapter.render_command_string("curl -o {{filename|output.txt}} {{url}}")
    assert rendered_default == "curl -o output.txt http://100.85.12.34:8080"


def test_arsenal_interactive_commands():
    adapter = ArsenalAdapter()
    res_set = adapter.handle_command("set target=10.10.10.50")
    assert res_set is not None and "10.10.10.50" in res_set
    assert adapter.get_variable("target") == "10.10.10.50"

    res_vars = adapter.handle_command("variables")
    assert res_vars is not None and "10.10.10.50" in res_vars

    res_tools = adapter.handle_command("tools")
    assert res_tools is not None and "curl" in res_tools


def test_arsenal_empty_query():
    adapter = ArsenalAdapter()
    all_cmds = adapter.search("")
    assert len(all_cmds) == len(adapter._commands_cache)


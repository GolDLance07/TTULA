"""Tests for Legba Adapter."""

import pytest
from ttula.core.models import Target
from ttula.integrations.legba.adapter import LegbaAdapter


def test_legba_refuses_unauthorized_target():
    adapter = LegbaAdapter()
    unauthorized_target = Target(name="unknown_peer", tailscale_ip="100.64.0.99", is_authorized_lab=False)

    with pytest.raises(PermissionError) as exc_info:
        adapter.build_command(protocol="ssh", target=unauthorized_target, username="root", password="toor")
    assert "SAFETY GATE TRIGGERED" in str(exc_info.value)


def test_legba_builds_valid_ssh_command():
    adapter = LegbaAdapter()
    authorized_target = Target(name="lab_box", tailscale_ip="100.64.0.50", is_authorized_lab=True)

    cmd = adapter.build_command(
        protocol="ssh",
        target=authorized_target,
        username="admin",
        password="secretpassword",
        port=2222,
        concurrency=3,
    )
    assert cmd.requires_authorized_lab is True
    assert cmd.source_tool == "legba"
    assert cmd.argv == [
        "legba",
        "ssh",
        "--target",
        "100.64.0.50",
        "--port",
        "2222",
        "--username",
        "admin",
        "--password",
        "secretpassword",
        "-c",
        "3",
    ]


def test_legba_builds_http_command_with_wordlist():
    adapter = LegbaAdapter()
    authorized_target = Target(name="lab_web", tailscale_ip="100.64.0.50", is_authorized_lab=True)

    cmd = adapter.build_command(
        protocol="http",
        target=authorized_target,
        username="admin",
        wordlist_pass="/usr/share/wordlists/rockyou.txt",
        port=8080,
    )
    assert cmd.argv[0] == "legba"
    assert cmd.argv[1] == "http"
    assert "--target" in cmd.argv
    assert "http://100.64.0.50:8080" in cmd.argv
    assert "--wordlist-pass" in cmd.argv
    assert "/usr/share/wordlists/rockyou.txt" in cmd.argv

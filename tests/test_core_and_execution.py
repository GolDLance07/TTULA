"""Tests for TTULA Core Models and Execution Manager."""

import pytest
from ttula.core.models import (
    Command,
    ExecutionNode,
    Operation,
    Target,
    TerminalSession,
    ToolResult,
    URLCollection,
)
from ttula.core.operations import OperationRegistry, fill_command_placeholders
from ttula.execution.manager import get_execution_manager
from ttula.execution.process import run_process_command


def test_target_lab_authorization():
    t1 = Target(name="untrusted_host", tailscale_ip="100.64.0.10", is_authorized_lab=False)
    assert not t1.validate_lab_authorization()

    t2 = Target(name="authorized_vuln_lab", tailscale_ip="100.64.0.20", is_authorized_lab=True)
    assert t2.validate_lab_authorization()


def test_command_argv_validation():
    # Valid command
    cmd = Command(
        source_tool="test",
        title="Test echo",
        description="Prints hello",
        argv=["echo", "hello"],
    )
    assert cmd.argv == ["echo", "hello"]
    assert "echo hello" in cmd.display_string

    # Invalid argv type
    with pytest.raises(TypeError):
        Command(
            source_tool="test",
            title="Bad",
            description="Bad",
            argv="echo hello",  # type: ignore
        )


def test_fill_command_placeholders():
    target = Target(name="lab_box", tailscale_ip="100.100.1.5", is_authorized_lab=True)
    cmd = Command(
        source_tool="arsenal",
        title="Nmap Port Scan",
        description="Scan lab",
        argv=["nmap", "-sV", "<target>", "-p", "<port>"],
        requires_authorized_lab=True,
    )
    filled = fill_command_placeholders(cmd, target=target, extra_params={"port": "8080"})
    assert filled.argv == ["nmap", "-sV", "100.100.1.5", "-p", "8080"]


def test_fill_command_placeholders_safety_gate():
    unauthorized = Target(name="rogue_box", tailscale_ip="100.100.1.99", is_authorized_lab=False)
    cmd = Command(
        source_tool="legba",
        title="Auth Test",
        description="Auth attack",
        argv=["legba", "ssh", "--target", "<target>"],
        requires_authorized_lab=True,
    )
    with pytest.raises(PermissionError):
        fill_command_placeholders(cmd, target=unauthorized)


def test_process_runner():
    res = run_process_command(["python", "-c", "print('TTULA_PROCESS_OK')"])
    assert res.success
    assert "TTULA_PROCESS_OK" in res.stdout


def test_execution_manager_singleton_and_continuity():
    em1 = get_execution_manager()
    em2 = get_execution_manager()
    assert em1 is em2

    node = ExecutionNode(name="local", local=True)
    session = em1.create_session(node, session_id="test_seq_session")
    assert session.alive

    # Send 5 sequential commands and verify counter
    for i in range(5):
        em1.send("test_seq_session", f"echo SEQ_CHECK_{i}")

    assert em1.get_command_count("test_seq_session") >= 5
    out = em1.read("test_seq_session", timeout=1.0)
    assert "SEQ_CHECK" in out

    em1.kill("test_seq_session")
    assert not em1.get_session("test_seq_session").alive

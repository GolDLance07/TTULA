"""Full End-to-End Workflow Integration Test for TTULA.

Executes complete workflow:
1. Tailscale inspection and node discovery
2. Lab target explicit authorization
3. Tookie OSINT discovery
4. Uro URL pipeline processing
5. Arsenal command discovery & placeholder substitution
6. Legba auth command preparation with strict safety gates
7. Persistent PTY dispatch and output verification
"""

import pytest
from ttula.core.engine import create_default_engine
from ttula.core.models import Target
from ttula.execution.manager import get_execution_manager


def test_complete_end_to_end_orchestration_workflow(monkeypatch, tmp_path):
    # Set isolated test config dir
    monkeypatch.setenv("TTULA_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("TTULA_TMP_DIR", str(tmp_path / "tmp"))

    # Initialize Engine with simulated tailnet and native Uro
    engine = create_default_engine(mock_tailscale=True, force_native_uro=True)
    exec_mgr = get_execution_manager()

    # Step 1: Tailscale Check
    status = engine.get_tailscale_status()
    assert status["online"] is True
    assert status["device_count"] >= 2

    # Step 2: Identify Lab Target and Explicitly Authorize
    targets = engine.list_targets()
    lab = next(t for t in targets if t.name == "lab-vulnerable-server")
    assert not lab.is_authorized_lab  # Initially unauthorized

    engine.set_target_authorization(lab.name, True)
    authorized_lab = engine.get_target(lab.name)
    assert authorized_lab.is_authorized_lab is True
    assert authorized_lab.validate_lab_authorization()

    # Step 3 & 4: Tookie OSINT -> Uro Pipeline
    pipeline_res = engine.run_tookie_uro_pipeline("vulnerable_lab_admin")
    assert pipeline_res["raw_count"] > 0
    assert pipeline_res["cleaned_count"] > 0
    cleaned_urls = pipeline_res["cleaned_collection"].items
    assert len(cleaned_urls) > 0

    # Step 5: Arsenal Knowledge Search and Placeholder Substitution
    cheats = engine.find_commands("nmap service")
    assert len(cheats) > 0
    nmap_cmd = cheats[0]

    prepared_cmd = engine.prepare_command(
        nmap_cmd,
        target=authorized_lab,
        extra_params={"port": "80"},
    )
    assert authorized_lab.tailscale_ip in prepared_cmd.argv
    assert prepared_cmd.display_string.startswith("nmap")

    # Step 6: Legba Auth Command Construction (Authorized)
    legba_cmd = engine.build_legba_command(
        protocol="ssh",
        target=authorized_lab,
        username="admin",
        password="testpassword",
        port=2222,
        concurrency=2,
    )
    assert legba_cmd.requires_authorized_lab is True
    assert legba_cmd.argv == [
        "legba",
        "ssh",
        "--target",
        authorized_lab.tailscale_ip,
        "--port",
        "2222",
        "--username",
        "admin",
        "--password",
        "testpassword",
        "-c",
        "2",
    ]

    # Step 7: Verify Legba Refuses Unauthorized Target
    rogue_target = Target(name="rogue_external_node", tailscale_ip="192.168.1.100", is_authorized_lab=False)
    with pytest.raises(PermissionError):
        engine.build_legba_command(
            protocol="ssh",
            target=rogue_target,
            username="admin",
            password="test",
        )

    # Step 8: Execution in Persistent PTY
    node = engine.get_default_execution_node()
    session = exec_mgr.create_session(node, session_id="workflow_test_session")
    assert session.alive

    # Send echo command through session
    exec_mgr.send("workflow_test_session", "echo WORKFLOW_TEST_COMPLETE_SUCCESS")
    output = exec_mgr.read("workflow_test_session", timeout=1.0)
    assert "WORKFLOW_TEST_COMPLETE_SUCCESS" in output

    exec_mgr.kill("workflow_test_session")

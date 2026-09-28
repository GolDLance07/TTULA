"""Tests for TTULA Default Engine."""

from ttula.core.engine import create_default_engine
from ttula.core.models import Target


def test_default_engine_wiring(monkeypatch, tmp_path):
    monkeypatch.setenv("TTULA_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("TTULA_TMP_DIR", str(tmp_path / "tmp"))
    engine = create_default_engine(mock_tailscale=True, force_native_uro=True)
    assert engine.tailscale is not None
    assert engine.arsenal is not None
    assert engine.tookie is not None
    assert engine.uro is not None
    assert engine.legba is not None
    assert engine.execution_manager is not None

    targets = engine.list_targets()
    assert len(targets) > 0

    # Test lab authorization flow
    target_name = targets[0].name
    engine.set_target_authorization(target_name, True)
    assert engine.get_target(target_name).is_authorized_lab is True

    # Test find commands
    cmds = engine.find_commands("nmap")
    assert len(cmds) > 0

    # Test prepare command with authorized target
    lab_target = engine.get_target(target_name)
    prepared = engine.prepare_command(cmds[0], target=lab_target)
    assert lab_target.tailscale_ip in prepared.argv or lab_target.name in prepared.argv

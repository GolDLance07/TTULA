"""Tests for Tailscale Adapter."""

import tempfile
from pathlib import Path
from ttula.integrations.tailscale.adapter import TailscaleAdapter


def test_tailscale_mock_mode_and_authorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = TailscaleAdapter(config_path=tmpdir, mock_mode=True)
        status = adapter.get_status()
        assert status["online"] is True
        assert status["device_count"] == 3

        targets = adapter.get_targets()
        assert len(targets) == 2

        # Lab should not be authorized automatically
        lab_target = next(t for t in targets if t.name == "lab-vulnerable-server")
        assert lab_target.is_authorized_lab is False

        # Explicitly authorize
        adapter.save_lab_authorization("lab-vulnerable-server", True)
        assert adapter.is_authorized("lab-vulnerable-server") is True

        # Re-fetch targets and verify
        updated_targets = adapter.get_targets()
        updated_lab = next(t for t in updated_targets if t.name == "lab-vulnerable-server")
        assert updated_lab.is_authorized_lab is True


def test_tailscale_offline_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Point to non-existent tailscale binary to test graceful degradation
        adapter = TailscaleAdapter(config_path=tmpdir, tailscale_bin="non_existent_tailscale_bin", mock_mode=False)
        status = adapter.get_status()
        assert status["online"] is False
        assert len(status["devices"]) == 1  # only fallback local node

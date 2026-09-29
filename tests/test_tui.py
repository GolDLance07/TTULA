"""Tests for TTULA Visual Terminal Dashboard (TUI)."""

import pytest
from ttula.ui.tui.app import TTULATUIApp
from ttula.core.models import Target


@pytest.mark.anyio
async def test_tui_app_mount_and_tabs(monkeypatch, tmp_path):
    monkeypatch.setenv("TTULA_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("TTULA_TMP_DIR", str(tmp_path / "tmp"))

    app = TTULATUIApp()
    # Force mock tailscale in test
    app.engine.tailscale.mock_mode = True

    async with app.run_test() as pilot:
        # Verify title and initial tab
        assert "TTULA" in app.title
        assert app.active_target is not None

        # Verify devices table has rows from mock tailscale
        table = app.query_one("#devices_table")
        assert table.row_count > 0

        # Test spacebar to toggle authorization
        initial_auth = app.active_target.is_authorized_lab
        app.action_toggle_auth()
        assert app.active_target.is_authorized_lab != initial_auth

        # Test tab switching
        app.action_switch_tab("tab_tookie")
        tabs = app.query_one("#main_tabs")
        assert tabs.active == "tab_tookie"

        app.action_switch_tab("tab_arsenal")
        assert tabs.active == "tab_arsenal"

        app.action_switch_tab("tab_legba")
        assert tabs.active == "tab_legba"

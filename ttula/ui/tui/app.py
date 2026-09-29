"""TTULA Visual Terminal User Interface (TUI).

Full terminal dashboard built with Textual, featuring:
- Real-time Tailscale mesh monitoring & 1-key lab authorization toggle
- Multi-tool pipeline (Tookie -> Uro -> Arsenal -> Legba)
- Live persistent interactive PTY split pane
"""

from __future__ import annotations
import os
import sys
import time
from typing import Optional, List, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Static,
    Button,
    Input,
    Label,
    DataTable,
    RichLog,
    Select,
    Switch,
)
from textual.reactive import reactive
from textual.binding import Binding

from ttula.core.engine import TTULAEngine, create_default_engine
from ttula.core.models import Target, Command, URLCollection
from ttula.execution.manager import get_execution_manager


class TTULATUIApp(App):
    """Main Textual Application for TTULA."""

    TITLE = "TTULA // SecOps Terminal Orchestrator"
    SUB_TITLE = "Personal Kali-Native Lab Orchestration"
    CSS = """
    Screen {
        background: #0b0f19;
        color: #e2e8f0;
    }

    Header {
        background: #06090e;
        color: #00f0ff;
        dock: top;
    }

    Footer {
        background: #06090e;
        color: #94a3b8;
        dock: bottom;
    }

    #status_bar {
        background: #111827;
        color: #38bdf8;
        border-bottom: solid #00f0ff;
        padding: 0 1;
        height: 3;
    }

    .glass-box {
        background: #131b2e;
        border: round #1e293b;
        padding: 1;
        margin: 1;
    }

    .card-title {
        color: #00f0ff;
        text-style: bold;
        margin-bottom: 1;
    }

    .cmd-preview {
        background: #06090e;
        color: #38bdf8;
        border: solid #00f0ff;
        padding: 1;
        margin: 1 0;
        text-style: bold;
    }

    .badge-auth {
        color: #00ff88;
        text-style: bold;
    }

    .badge-unauth {
        color: #ef4444;
        text-style: bold;
    }

    #terminal_pane {
        height: 12;
        border-top: double #00f0ff;
        background: #06090e;
    }

    #term_log {
        background: #06090e;
        color: #38bdf8;
        height: 8;
    }

    #term_input {
        background: #111827;
        color: #e2e8f0;
        border: tall #1e293b;
    }

    Button {
        margin: 0 1;
    }

    DataTable {
        height: 100%;
        background: #131b2e;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("1", "switch_tab('tab_tailscale')", "Tailscale", show=True),
        Binding("2", "switch_tab('tab_tookie')", "Tookie", show=True),
        Binding("3", "switch_tab('tab_uro')", "Uro", show=True),
        Binding("4", "switch_tab('tab_arsenal')", "Arsenal", show=True),
        Binding("5", "switch_tab('tab_legba')", "Legba", show=True),
        Binding("space", "toggle_auth", "Toggle Lab Auth", show=True),
        Binding("r", "refresh_tailscale", "Refresh", show=True),
    ]

    active_target: reactive[Optional[Target]] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine: TTULAEngine = create_default_engine(mock_tailscale=False, force_native_uro=False)
        self.exec_mgr = get_execution_manager()
        self.session_id = "ttula_tui_pty"
        self.pty_session = self.exec_mgr.create_session(
            self.engine.get_default_execution_node(), session_id=self.session_id
        )
        self._last_collection: Optional[URLCollection] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="status_bar")

        with TabbedContent(initial="tab_tailscale", id="main_tabs"):
            # TAB 1: TAILSCALE MESH
            with TabPane("🌐 [1] Tailnet Mesh", id="tab_tailscale"):
                with Vertical(classes="glass-box"):
                    yield Label("Discovered Tailscale Lab Mesh Devices", classes="card-title")
                    yield DataTable(id="devices_table")
                    with Horizontal():
                        yield Button("Toggle Lab Authorization (Space)", id="btn_toggle_auth", variant="primary")
                        yield Button("Set Active Target (Enter)", id="btn_set_target", variant="success")
                        yield Button("Refresh Status (r)", id="btn_refresh_ts")
                        yield Button("Simulate Lab Node", id="btn_sim_node")

            # TAB 2: TOOKIE OSINT
            with TabPane("🔍 [2] Tookie OSINT", id="tab_tookie"):
                with Vertical(classes="glass-box"):
                    yield Label("OSINT Username Discovery", classes="card-title")
                    with Horizontal():
                        yield Input(placeholder="Target username (e.g. labadmin)", id="input_tookie_user")
                        yield Button("🚀 Run Discovery", id="btn_run_tookie", variant="primary")
                    yield DataTable(id="tookie_results_table")
                    with Horizontal():
                        yield Button("🧹 Send Collection to Uro Pipeline", id="btn_tookie_to_uro", variant="success")

            # TAB 3: URO FILTERING
            with TabPane("🧹 [3] Uro URL Filter", id="tab_uro"):
                with Vertical(classes="glass-box"):
                    yield Label("URL Cleaning and Normalization", classes="card-title")
                    yield Static("Ready to filter URL collection...", id="uro_status_label")
                    yield DataTable(id="uro_results_table")
                    with Horizontal():
                        yield Button("⚡ Clean URLs with Uro", id="btn_run_uro", variant="primary")

            # TAB 4: ARSENAL CHEATS
            with TabPane("📚 [4] Arsenal Cheats", id="tab_arsenal"):
                with Vertical(classes="glass-box"):
                    yield Label("Curated Command Playbooks", classes="card-title")
                    with Horizontal():
                        yield Input(placeholder="Search tag or query (e.g. nmap, web, scan)", id="input_arsenal_query")
                        yield Button("🔍 Search", id="btn_search_arsenal", variant="primary")
                    yield DataTable(id="arsenal_table")
                    yield Static("$ [Select a command template above]", id="arsenal_cmd_preview", classes="cmd-preview")
                    with Horizontal():
                        yield Button("▶ Execute in PTY Terminal", id="btn_exec_arsenal", variant="success")

            # TAB 5: LEGBA AUTH TESTING
            with TabPane("🔐 [5] Legba Auth", id="tab_legba"):
                with Vertical(classes="glass-box"):
                    yield Label("Legba Authentication Testing (Strict Lab Gated)", classes="card-title")
                    yield Static("⚠️ Refuses execution unless target is marked [✓ AUTHORIZED LAB]", id="legba_warning")
                    with Horizontal():
                        yield Select(
                            options=[("SSH", "ssh"), ("HTTP", "http"), ("SMB", "smb"), ("FTP", "ftp")],
                            value="ssh",
                            id="select_legba_proto",
                        )
                        yield Input(placeholder="Port (22 or 80)", value="22", id="input_legba_port")
                        yield Input(placeholder="Username", value="admin", id="input_legba_user")
                        yield Input(placeholder="Password", value="password123", id="input_legba_pass", password=True)
                    yield Static("$ [Select target and protocol]", id="legba_cmd_preview", classes="cmd-preview")
                    with Horizontal():
                        yield Button("🚀 Launch Legba Auth Test in PTY", id="btn_exec_legba", variant="error")

        # BOTTOM SPLIT: PERSISTENT PTY TERMINAL
        with Vertical(id="terminal_pane"):
            yield Label("💻 Live Persistent PTY Console Stream (survives interactions)", id="lbl_pty_title")
            yield RichLog(id="term_log", highlight=True, markup=True)
            with Horizontal():
                yield Input(placeholder="Send raw command to PTY (e.g. echo $USER or tailscale netcheck)", id="term_input")
                yield Button("Send ⏎", id="btn_send_pty", variant="primary")
                yield Button("Clear", id="btn_clear_pty")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize tables and periodic background reading."""
        # Setup Devices Table
        dt_devices = self.query_one("#devices_table", DataTable)
        dt_devices.cursor_type = "row"
        dt_devices.add_columns("Device Name", "Tailscale IP", "OS", "Status", "Authorization")

        # Setup Tookie Table
        dt_tookie = self.query_one("#tookie_results_table", DataTable)
        dt_tookie.cursor_type = "row"
        dt_tookie.add_columns("Platform", "Discovered URL", "Match Status")

        # Setup Uro Table
        dt_uro = self.query_one("#uro_results_table", DataTable)
        dt_uro.cursor_type = "row"
        dt_uro.add_columns("Cleaned & Deduplicated Endpoints")

        # Setup Arsenal Table
        dt_arsenal = self.query_one("#arsenal_table", DataTable)
        dt_arsenal.cursor_type = "row"
        dt_arsenal.add_columns("Title", "Tool", "Description")

        # Log initial terminal banner
        term_log = self.query_one("#term_log", RichLog)
        term_log.write("[bold cyan][*] TTULA Interactive PTY Session active. Zero-injection argv executor ready.[/bold cyan]")

        # Initial refresh
        self.action_refresh_tailscale()
        self._populate_arsenal()

        # Set periodic timer to read PTY output stream
        self.set_interval(0.2, self._poll_pty_output)

    def _poll_pty_output(self) -> None:
        """Reads real-time output chunks from the persistent PTY."""
        try:
            chunk = self.exec_mgr.read(self.session_id, timeout=0.05)
            if chunk:
                term_log = self.query_one("#term_log", RichLog)
                term_log.write(chunk.strip())
        except Exception:
            pass

    def watch_active_target(self, target: Optional[Target]) -> None:
        """Update status bar whenever active target changes."""
        self._update_status_bar()
        self._update_legba_preview()
        self._update_arsenal_preview()

    def _update_status_bar(self) -> None:
        status = self.engine.get_tailscale_status()
        online = status.get("online", False)
        self_ip = status.get("self_ip", "127.0.0.1")

        target_str = "[dim]None selected[/dim]"
        if self.active_target:
            auth_str = "[bold green][✓ LAB][/bold green]" if self.active_target.is_authorized_lab else "[bold red][✗ RESTRICTED][/bold red]"
            target_str = f"[bold cyan]{self.active_target.name}[/bold cyan] ({self.active_target.tailscale_ip}) {auth_str}"

        online_badge = "[bold green]ONLINE[/bold green]" if online else "[bold yellow]STANDALONE/OFFLINE[/bold yellow]"
        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(
            f" Mesh Status: {online_badge} | Node IP: [bold]{self_ip}[/bold] | Active Target: {target_str}"
        )

    def action_refresh_tailscale(self) -> None:
        """Fetch latest devices from Tailscale adapter and update UI table."""
        dt = self.query_one("#devices_table", DataTable)
        dt.clear()

        targets = self.engine.list_targets()
        for t in targets:
            auth_display = "[bold green]✓ AUTHORIZED LAB[/bold green]" if t.is_authorized_lab else "[bold red]✗ RESTRICTED[/bold red]"
            status_display = "[green]ONLINE[/green]"
            dt.add_row(t.name, t.tailscale_ip, t.os or "linux", status_display, auth_display, key=t.name)

        if targets and self.active_target is None:
            self.active_target = targets[0]

        self._update_status_bar()

    def action_toggle_auth(self) -> None:
        """Toggle authorization of highlighted device in table."""
        dt = self.query_one("#devices_table", DataTable)
        if dt.row_count == 0:
            return

        cursor_row = dt.cursor_row
        row_key, _ = dt.coordinate_to_cell_key(dt.cursor_coordinate)
        target_name = str(row_key.value)

        target = self.engine.get_target(target_name)
        if target:
            new_auth = not target.is_authorized_lab
            self.engine.set_target_authorization(target.name, new_auth)
            if self.active_target and self.active_target.name == target.name:
                self.active_target = target
            self.action_refresh_tailscale()

    def action_switch_tab(self, tab_id: str) -> None:
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = tab_id

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_refresh_ts":
            self.action_refresh_tailscale()
        elif btn_id == "btn_toggle_auth":
            self.action_toggle_auth()
        elif btn_id == "btn_set_target":
            dt = self.query_one("#devices_table", DataTable)
            if dt.row_count > 0:
                row_key, _ = dt.coordinate_to_cell_key(dt.cursor_coordinate)
                target = self.engine.get_target(str(row_key.value))
                if target:
                    self.active_target = target
                    self.notify(f"Active target locked: {target.name} ({target.tailscale_ip})")
        elif btn_id == "btn_sim_node":
            sim = Target(name="lab-vulnerable-server", tailscale_ip="100.64.0.50", is_authorized_lab=True, os="linux")
            self.engine.register_target(sim)
            self.active_target = sim
            self.action_refresh_tailscale()
            self.notify("Simulated authorized lab node registered.")
        elif btn_id == "btn_run_tookie":
            self._handle_tookie_run()
        elif btn_id == "btn_tookie_to_uro":
            self._handle_tookie_to_uro()
        elif btn_id == "btn_run_uro":
            self._handle_uro_run()
        elif btn_id == "btn_search_arsenal":
            self._populate_arsenal()
        elif btn_id == "btn_exec_arsenal":
            self._execute_selected_arsenal()
        elif btn_id == "btn_exec_legba":
            self._execute_legba()
        elif btn_id == "btn_send_pty":
            self._send_pty_input()
        elif btn_id == "btn_clear_pty":
            self.query_one("#term_log", RichLog).clear()

    def _handle_tookie_run(self) -> None:
        inp = self.query_one("#input_tookie_user", Input)
        user = inp.value.strip()
        if not user:
            self.notify("Please enter a username to discover.", severity="warning")
            return

        self.notify(f"Running Tookie discovery for '{user}'...")
        try:
            col = self.engine.run_tookie(user, timeout=30)
            self._last_collection = col
            dt = self.query_one("#tookie_results_table", DataTable)
            dt.clear()

            matches = col.metadata.get("matches", [])
            for m in matches:
                dt.add_row(m.get("platform", "Web"), m.get("url", ""), m.get("status", "possible match"))

            self.notify(f"Tookie found {col.count()} URLs. You can now send them to Uro.")
        except Exception as e:
            self.notify(f"Tookie error: {e}", severity="error")

    def _handle_tookie_to_uro(self) -> None:
        if not self._last_collection or not self._last_collection.items:
            self.notify("No Tookie results to process. Run discovery first.", severity="warning")
            return

        self.action_switch_tab("tab_uro")
        self._handle_uro_run()

    def _handle_uro_run(self) -> None:
        if not self._last_collection:
            self.notify("No collection available for Uro.", severity="warning")
            return

        try:
            cleaned = self.engine.run_uro(self._last_collection)
            self._last_collection = cleaned
            lbl = self.query_one("#uro_status_label", Static)
            lbl.update(f"[bold green]Deduplicated:[/bold green] {len(self._last_collection.items)} endpoints retained.")

            dt = self.query_one("#uro_results_table", DataTable)
            dt.clear()
            for u in cleaned.items:
                dt.add_row(u)
            self.notify(f"Uro cleaned {len(cleaned.items)} URLs.")
        except Exception as e:
            self.notify(f"Uro error: {e}", severity="error")

    def _populate_arsenal(self) -> None:
        inp = self.query_one("#input_arsenal_query", Input)
        query = inp.value.strip()
        cmds = self.engine.find_commands(query)

        dt = self.query_one("#arsenal_table", DataTable)
        dt.clear()
        for i, cmd in enumerate(cmds):
            dt.add_row(cmd.title, cmd.source_tool, cmd.description, key=str(i))

        if cmds:
            self._current_cmds = cmds
            self._update_arsenal_preview()

    def _update_arsenal_preview(self) -> None:
        if not hasattr(self, "_current_cmds") or not self._current_cmds:
            return
        cmd = self._current_cmds[0]
        try:
            prep = self.engine.prepare_command(cmd, target=self.active_target)
            self.query_one("#arsenal_cmd_preview", Static).update(f"$ {prep.display_string}")
        except Exception as e:
            self.query_one("#arsenal_cmd_preview", Static).update(f"⛔ {e}")

    def _execute_selected_arsenal(self) -> None:
        dt = self.query_one("#arsenal_table", DataTable)
        if dt.row_count == 0 or not hasattr(self, "_current_cmds"):
            return

        row_idx = dt.cursor_row
        if row_idx < len(self._current_cmds):
            cmd = self._current_cmds[row_idx]
            try:
                prep = self.engine.prepare_command(cmd, target=self.active_target)
                self.exec_mgr.send(self.session_id, prep)
                self.query_one("#term_log", RichLog).write(f"\n[bold green]$ {prep.display_string}[/bold green]")
                self.notify(f"Dispatched '{prep.title}' to live PTY.")
            except Exception as e:
                self.notify(f"Safety Gate: {e}", severity="error")

    def _update_legba_preview(self) -> None:
        if not self.active_target:
            self.query_one("#legba_cmd_preview", Static).update("⛔ No active target selected. Go to [1] Tailscale.")
            return

        proto = self.query_one("#select_legba_proto", Select).value or "ssh"
        port = int(self.query_one("#input_legba_port", Input).value or 22)
        user = self.query_one("#input_legba_user", Input).value
        pw = self.query_one("#input_legba_pass", Input).value

        try:
            cmd = self.engine.build_legba_command(
                protocol=str(proto),
                target=self.active_target,
                username=user,
                password=pw,
                port=port,
                concurrency=2,
            )
            self.query_one("#legba_cmd_preview", Static).update(f"$ {cmd.display_string}")
        except Exception as e:
            self.query_one("#legba_cmd_preview", Static).update(f"⛔ {e}")

    def _execute_legba(self) -> None:
        if not self.active_target:
            self.notify("No active target selected.", severity="error")
            return

        proto = self.query_one("#select_legba_proto", Select).value or "ssh"
        port = int(self.query_one("#input_legba_port", Input).value or 22)
        user = self.query_one("#input_legba_user", Input).value
        pw = self.query_one("#input_legba_pass", Input).value

        try:
            cmd = self.engine.build_legba_command(
                protocol=str(proto),
                target=self.active_target,
                username=user,
                password=pw,
                port=port,
                concurrency=2,
            )
            self.exec_mgr.send(self.session_id, cmd)
            self.query_one("#term_log", RichLog).write(f"\n[bold red]$ {cmd.display_string}[/bold red]")
            self.notify(f"Dispatched Legba {proto.upper()} attack to persistent PTY.")
        except Exception as e:
            self.notify(f"Safety Gate Refused Execution: {e}", severity="error")

    def _send_pty_input(self) -> None:
        inp = self.query_one("#term_input", Input)
        val = inp.value.strip()
        if val:
            self.exec_mgr.send(self.session_id, val)
            self.query_one("#term_log", RichLog).write(f"$ {val}")
            inp.value = ""


def run_tui():
    """Entry point for the TUI."""
    app = TTULATUIApp()
    app.run()


if __name__ == "__main__":
    run_tui()

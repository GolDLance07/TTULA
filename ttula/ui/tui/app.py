"""TTULA Visual Terminal User Interface (TUI).

Full terminal dashboard built with Textual, featuring:
- Web Crawler endpoint discovery & crawling engine
- Arsenal-style tool headers and categorized badges
- Real-time Tailscale mesh monitoring & 1-key lab authorization toggle
- Multi-tool pipeline (Crawler -> Tookie -> Uro -> Arsenal -> Legba)
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
from textual import work

from ttula.core.engine import TTULAEngine, create_default_engine
from ttula.core.models import Target, Command, URLCollection
from ttula.execution.manager import get_execution_manager
from ttula.config.tools import TOOLS, CATEGORY_COLORS, get_tool_metadata
from rich.markup import escape


class TTULATUIApp(App):
    """Main Textual Application for Web Crawler."""

    TITLE = "TTULA // Web Crawler"
    SUB_TITLE = "Security Reconnaissance Workspace"
    CSS = """
    Screen {
        background: #0A0D12;
        color: #e2e8f0;
    }

    Header {
        background: #0A0D12;
        color: #10b981;
        dock: top;
        border-bottom: solid #232D3B;
    }

    Footer {
        background: #0A0D12;
        color: #94a3b8;
        dock: bottom;
        border-top: solid #232D3B;
    }

    #status_bar {
        background: #11161D;
        color: #34d399;
        border-bottom: solid #232D3B;
        padding: 0 1;
        height: 3;
    }

    #main_tabs {
        height: 1fr;
        background: #0A0D12;
    }

    TabbedContent Tabs {
        background: #11161D;
        border-bottom: solid #232D3B;
    }

    Tab {
        color: #94a3b8;
        background: #11161D;
    }

    Tab.-active {
        color: #34d399;
        background: #18202C;
        text-style: bold;
        border-bottom: tall #10b981;
    }

    .glass-box {
        background: #11161D;
        border: round #232D3B;
        padding: 0 1;
        height: 1fr;
    }

    .tool-header-title {
        color: #10b981;
        text-style: bold;
        height: 1;
    }

    .tool-header-tagline {
        color: #94a3b8;
        height: 1;
    }

    .tool-header-badges {
        height: 1;
        margin-bottom: 1;
    }

    /* Home Page Styles */
    .home-box {
        align: center middle;
        text-align: center;
        padding: 1;
        overflow-y: auto;
    }

    .home-brand-title {
        color: #10b981;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-top: 0;
    }

    .home-tagline {
        color: #34d399;
        text-align: center;
        width: 100%;
        margin-bottom: 0;
    }

    .home-summary {
        color: #94a3b8;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .home-steps {
        color: #cbd5e1;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .home-badges {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .home-divider {
        color: #232D3B;
        text-align: center;
        width: 100%;
    }

    .home-actions-row {
        align: center middle;
        height: 3;
        margin-top: 0;
    }

    .home-actions-row Button {
        margin: 0 1;
    }

    .home-footer-row {
        height: 2;
        margin-top: 1;
        width: 100%;
        align: right middle;
    }

    .home-footer-spacer {
        width: 1fr;
    }

    .home-creators-box {
        width: auto;
        padding-right: 2;
    }

    .home-creators-label {
        color: #64748B;
        text-align: right;
    }

    .home-creators-names {
        color: #10b981;
        text-style: bold;
        text-align: right;
    }

    .card-title {
        color: #10b981;
        text-style: bold;
        margin-bottom: 0;
        height: 1;
    }

    .input-row {
        height: 3;
        margin: 0 0 1 0;
    }

    .input-row Input {
        width: 1fr;
    }

    .input-row Button {
        width: auto;
    }

    #input_arsenal_port {
        width: 14;
    }

    #input_tookie_limit {
        width: 24;
    }

    #input_crawler_max_pages {
        width: 16;
    }

    .btn-row {
        height: 3;
        margin-top: 0;
    }

    .btn-row Button {
        margin-right: 1;
    }

    #arsenal_vars_status {
        height: 1;
        color: #34d399;
    }

    #input_arsenal_set_var {
        width: 28;
    }

    #arsenal_detail_row {
        height: 3;
        margin: 0;
    }

    #arsenal_cmd_preview {
        width: 1fr;
        height: 100%;
        background: #0A0D12;
        color: #10b981;
        border: solid #232D3B;
        padding: 0 1;
        text-style: bold;
    }

    #arsenal_cmd_desc {
        width: 1fr;
        height: 100%;
        background: #18202C;
        color: #94a3b8;
        border: solid #232D3B;
        padding: 0 1;
        overflow-y: scroll;
    }

    .cmd-preview {
        background: #0A0D12;
        color: #34d399;
        border: solid #232D3B;
        padding: 0 1;
        height: 3;
        text-style: bold;
    }

    .badge-auth {
        color: #10b981;
        text-style: bold;
    }

    .badge-unauth {
        color: #ef4444;
        text-style: bold;
    }

    Input {
        background: #18202C;
        color: #e2e8f0;
        border: tall #232D3B;
    }

    Input:focus {
        border: tall #10b981;
        background: #11161D;
        color: #ffffff;
    }

    DataTable {
        height: 1fr;
        min-height: 8;
        background: #11161D;
        border: solid #232D3B;
    }

    #terminal_pane {
        height: 7;
        border-top: solid #232D3B;
        background: #0A0D12;
    }

    #lbl_pty_title {
        height: 1;
        color: #34d399;
        text-style: bold;
    }

    #term_log {
        background: #0A0D12;
        color: #a7f3d0;
        height: 1fr;
        min-height: 3;
    }

    #term_input_row {
        height: 3;
    }

    #term_input {
        background: #18202C;
        color: #e2e8f0;
        border: tall #232D3B;
        width: 1fr;
    }

    #term_input:focus {
        border: tall #10b981;
        background: #11161D;
    }

    Button {
        margin: 0;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f1", "switch_tab('tab_home')", "F1 Home", show=True),
        Binding("f2", "switch_tab('tab_crawler')", "F2 Crawl", show=True),
        Binding("f3", "switch_tab('tab_tailscale')", "F3 Mesh", show=True),
        Binding("f4", "switch_tab('tab_tookie')", "F4 OSINT", show=True),
        Binding("f5", "switch_tab('tab_uro')", "F5 Uro", show=True),
        Binding("f6", "switch_tab('tab_arsenal')", "F6 Arsenal", show=True),
        Binding("f7", "switch_tab('tab_legba')", "F7 Auth", show=True),
        Binding("0", "key_0", "0", show=False),
        Binding("1", "key_1", "1", show=False),
        Binding("2", "key_2", "2", show=False),
        Binding("3", "key_3", "3", show=False),
        Binding("4", "key_4", "4", show=False),
        Binding("5", "key_5", "5", show=False),
        Binding("6", "key_6", "6", show=False),
        Binding("space", "key_space", "Space Auth", show=True),
        Binding("r", "key_refresh", "r Refresh", show=True),
        Binding("f12", "focus_terminal", "F12 Terminal", show=True),
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
            # TAB 0: HOME
            with TabPane("⌂ [0] Home", id="tab_home"):
                with Vertical(classes="glass-box home-box"):
                    yield Label("WEB CRAWLER", classes="home-brand-title")
                    yield Label(
                        "Unified Security Reconnaissance Workspace",
                        classes="home-tagline",
                    )
                    yield Static(
                        "Automated attack surface mapping, deep endpoint crawling, "
                        "identity discovery, URL processing, and zero-trust lab gating.",
                        classes="home-summary",
                    )
                    yield Static("─" * 60, classes="home-divider")
                    yield Static(
                        "[bold #10b981]Steps to Use:[/bold #10b981]\n"
                        "[dim]1.[/dim] [bold]Discover[/bold] – Crawl target web endpoints or run Tookie identity OSINT\n"
                        "[dim]2.[/dim] [bold]Clean[/bold] – Pipe endpoints into Uro to deduplicate and strip noise\n"
                        "[dim]3.[/dim] [bold]Select[/bold] – Browse 247+ tools & YAML commands in Arsenal-NG\n"
                        "[dim]4.[/dim] [bold]Execute[/bold] – Dispatch safely to the live persistent PTY terminal",
                        classes="home-steps",
                    )
                    yield Static("─" * 60, classes="home-divider")
                    with Horizontal(classes="home-actions-row"):
                        yield Button("🕸️ Start Crawling", id="btn_home_crawl", variant="primary")
                        yield Button("🔍 Identity OSINT", id="btn_home_tookie")
                        yield Button("📚 Security Cheats", id="btn_home_arsenal")
                        yield Button("🌐 Tailnet Mesh", id="btn_home_mesh")
                    yield Static("─" * 60, classes="home-divider")
                    with Horizontal(classes="home-footer-row"):
                        yield Static(" ", classes="home-footer-spacer")
                        with Vertical(classes="home-creators-box"):
                            yield Label("Created by", classes="home-creators-label")
                            yield Label("Aarush Rahul Patel · Shreya Singh", classes="home-creators-names")

            # TAB 1: WEB CRAWLER
            with TabPane("🕸️ [1] Web Crawler", id="tab_crawler"):
                with Vertical(classes="glass-box"):
                    yield Label("WEB CRAWLER", classes="tool-header-title")
                    yield Label("Web crawling and endpoint discovery", classes="tool-header-tagline")
                    yield Static(
                        "[bold #10b981][ WEB RECON ][/]  "
                        "[bold #34d399][ INFORMATION GATHERING ][/]  "
                        "[bold #64748b][ RECON ][/]",
                        classes="tool-header-badges",
                    )
                    with Horizontal(classes="input-row"):
                        yield Input(placeholder="Target URL (e.g. http://127.0.0.1:8000)", id="input_crawler_url")
                        yield Input(placeholder="Max Pages (e.g. 15)", value="15", id="input_crawler_max_pages")
                        yield Button("🕸️ Start Crawl", id="btn_run_crawler", variant="primary")
                    yield DataTable(id="crawler_results_table")
                    with Horizontal(classes="btn-row"):
                        yield Button("🧹 Send Discovered URLs to Uro Pipeline", id="btn_crawler_to_uro", variant="success")
                        yield Button("⚡ Crawl & Deduplicate (Auto-Pipe)", id="btn_crawler_pipe_uro")

            # TAB 2: TAILSCALE MESH
            with TabPane("🌐 [2] Tailnet Mesh", id="tab_tailscale"):
                with Vertical(classes="glass-box"):
                    yield Label("TAILSCALE", classes="tool-header-title")
                    yield Label("Secure peer-to-peer lab network boundary", classes="tool-header-tagline")
                    yield Static(
                        "[bold #10b981][ NETWORK RECON ][/]  "
                        "[bold #64748b][ SECURITY AUTOMATION ][/]",
                        classes="tool-header-badges",
                    )
                    yield DataTable(id="devices_table")
                    with Horizontal(classes="btn-row"):
                        yield Button("Toggle Lab Authorization (Space)", id="btn_toggle_auth", variant="primary")
                        yield Button("Set Active Target (Enter)", id="btn_set_target", variant="success")
                        yield Button("Refresh Status (r)", id="btn_refresh_ts")
                        yield Button("Simulate Lab Node", id="btn_sim_node")

            # TAB 3: TOOKIE OSINT
            with TabPane("🔍 [3] Tookie OSINT", id="tab_tookie"):
                with Vertical(classes="glass-box"):
                    yield Label("TOOKIE", classes="tool-header-title")
                    yield Label("Username and identity OSINT tool (60+ Platforms)", classes="tool-header-tagline")
                    yield Static(
                        "[bold #10b981][ OSINT ][/]  "
                        "[bold #34d399][ IDENTITY DISCOVERY ][/]  "
                        "[bold #64748b][ RECON ][/]",
                        classes="tool-header-badges",
                    )
                    with Horizontal(classes="input-row"):
                        yield Input(placeholder="Target username (e.g. labadmin, root)", id="input_tookie_user")
                        yield Input(placeholder="Max URLs (default 50)", value="50", id="input_tookie_limit")
                        yield Button("🚀 Run Discovery", id="btn_run_tookie", variant="primary")
                    yield DataTable(id="tookie_results_table")
                    with Horizontal(classes="btn-row"):
                        yield Button("🧹 Send Collection to Uro Pipeline", id="btn_tookie_to_uro", variant="success")

            # TAB 4: URO FILTERING
            with TabPane("🧹 [4] Uro URL Filter", id="tab_uro"):
                with Vertical(classes="glass-box"):
                    yield Label("URO", classes="tool-header-title")
                    yield Label("URL normalization and deduplication utility", classes="tool-header-tagline")
                    yield Static(
                        "[bold #10b981][ WEB RECON ][/]  "
                        "[bold #f59e0b][ URL PROCESSING ][/]  "
                        "[bold #64748b][ RECON ][/]",
                        classes="tool-header-badges",
                    )
                    yield Static("Ready to filter URL collection...", id="uro_status_label")
                    yield DataTable(id="uro_results_table")
                    with Horizontal(classes="btn-row"):
                        yield Button("⚡ Clean URLs with Uro", id="btn_run_uro", variant="primary")

            # TAB 5: ARSENAL-NG PLAYBOOKS
            with TabPane("📚 [5] Arsenal-NG", id="tab_arsenal"):
                with Vertical(classes="glass-box"):
                    with Horizontal(classes="input-row"):
                        yield Input(placeholder="Search Arsenal (e.g. nmap, curl, impacket, syn, smb, windapsearch)", id="input_arsenal_query")
                        yield Button("🔍 Search", id="btn_search_arsenal", variant="primary")
                        yield Input(placeholder="Set Var (e.g. port=8080, user=admin)", id="input_arsenal_set_var")
                        yield Button("💾 Set Var", id="btn_arsenal_set_var")
                        yield Button("Simulate Lab Target", id="btn_arsenal_sim_node")
                    yield DataTable(id="arsenal_table")
                    with Horizontal(id="arsenal_detail_row"):
                        yield Static("$ [Select a command template above]", id="arsenal_cmd_preview")
                        yield Static("[Select command for documentation]", id="arsenal_cmd_desc")
                    with Horizontal(classes="btn-row"):
                        yield Button("▶ Execute in PTY Terminal (Enter)", id="btn_exec_arsenal", variant="success")

            # TAB 6: LEGBA AUTH TESTING
            with TabPane("🔐 [6] Legba Auth", id="tab_legba"):
                with Vertical(classes="glass-box"):
                    yield Label("LEGBA", classes="tool-header-title")
                    yield Label("Multi-protocol authentication testing utility (Strict Lab Gated)", classes="tool-header-tagline")
                    yield Static(
                        "[bold #f43f5e][ AUTHENTICATION ][/]  "
                        "[bold #e11d48][ CREDENTIAL TESTING ][/]",
                        classes="tool-header-badges",
                    )
                    yield Static("⚠️ Refuses execution unless target is marked [✓ AUTHORIZED LAB]", id="legba_warning")
                    with Horizontal(classes="input-row"):
                        yield Select(
                            options=[("SSH", "ssh"), ("HTTP", "http"), ("SMB", "smb"), ("FTP", "ftp")],
                            value="ssh",
                            id="select_legba_proto",
                        )
                        yield Input(placeholder="Port (22 or 80)", value="22", id="input_legba_port")
                        yield Input(placeholder="Username", value="admin", id="input_legba_user")
                        yield Input(placeholder="Password", value="password123", id="input_legba_pass", password=True)
                    yield Static("$ [Select target and protocol]", id="legba_cmd_preview", classes="cmd-preview")
                    with Horizontal(classes="btn-row"):
                        yield Button("🚀 Launch Legba Auth Test in PTY", id="btn_exec_legba", variant="error")

        # BOTTOM SPLIT: PERSISTENT PTY TERMINAL
        with Vertical(id="terminal_pane"):
            yield Label("💻 Live Persistent PTY Console Stream (survives interactions)", id="lbl_pty_title")
            yield RichLog(id="term_log", highlight=True, markup=True)
            with Horizontal(id="term_input_row"):
                yield Input(placeholder="Send raw command to PTY (e.g. echo $USER or tailscale netcheck)", id="term_input")
                yield Button("Send ⏎", id="btn_send_pty", variant="primary")
                yield Button("Clear", id="btn_clear_pty")

        yield Footer()

    def _log_terminal(self, message: str) -> None:
        """Safely write to persistent PTY terminal RichLog without throwing NoMatches."""
        logs = self.query("#term_log")
        if logs:
            logs.first().write(message)

    def on_mount(self) -> None:
        """Initialize tables and periodic background reading."""
        # Setup Crawler Table
        dt_crawler = self.query_one("#crawler_results_table", DataTable)
        dt_crawler.cursor_type = "row"
        dt_crawler.add_columns("Discovered URL", "Depth", "Category", "Status")

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
        dt_arsenal.add_columns("Tool & Tags", "Action Title", "Requires Lab")

        # Log initial terminal banner
        self._log_terminal("[bold #10b981][*] TTULA Web Crawler PTY Session active. Zero-injection argv executor ready.[/bold #10b981]")

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
                self._log_terminal(chunk.strip())
        except Exception:
            pass

    def watch_active_target(self, target: Optional[Target]) -> None:
        """Update status bar, crawler URL, and Arsenal-NG session variables whenever active target changes."""
        if target:
            self.engine.set_session_variable("target", target.tailscale_ip)
            self.engine.set_session_variable("ip", target.tailscale_ip)
            self.engine.set_session_variable("host", target.tailscale_ip)
            self.engine.set_session_variable("rhost", target.tailscale_ip)
            self.engine.set_session_variable("hostname", target.hostname or target.name)
            port = self.engine.get_session_variables().get("port", "80")
            target_url = f"http://{target.tailscale_ip}:{port}"
            self.engine.set_session_variable("url", target_url)

            # Auto-populate crawler input if empty
            crawler_inputs = self.query("#input_crawler_url")
            if crawler_inputs and not crawler_inputs.first().value:
                crawler_inputs.first().value = target_url

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
            target_str = f"[bold #10b981]{self.active_target.name}[/bold #10b981] ({self.active_target.tailscale_ip}) {auth_str}"

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
            target.is_authorized_lab = new_auth
            if self.active_target and self.active_target.name == target.name:
                self.active_target.is_authorized_lab = new_auth

            auth_badge = "[bold green]AUTHORIZED LAB[/bold green]" if new_auth else "[bold red]RESTRICTED[/bold red]"
            self._log_terminal(f"\n[yellow][*] Security Boundary: target '{target.name}' updated to {auth_badge}[/yellow]")
            self.action_refresh_tailscale()
            self._update_status_bar()
            self._update_legba_preview()
            self._update_arsenal_preview()
            self.notify(f"Authorization toggled for {target.name}: {new_auth}")

    def action_key_0(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_home")

    def action_key_1(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_crawler")

    def action_key_2(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_tailscale")

    def action_key_3(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_tookie")

    def action_key_4(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_uro")

    def action_key_5(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_arsenal")

    def action_key_6(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_switch_tab("tab_legba")

    def action_key_space(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_toggle_auth()

    def action_key_refresh(self) -> None:
        if not isinstance(self.focused, Input):
            self.action_refresh_tailscale()

    def action_focus_terminal(self) -> None:
        self.query_one("#term_input", Input).focus()

    def action_switch_tab(self, tab_id: str) -> None:
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = tab_id
        self._focus_tab_widget(tab_id)

    def _focus_tab_widget(self, tab_id: str) -> None:
        target_widget = None
        if tab_id == "tab_home":
            btns = self.query("#btn_home_crawl")
            if btns:
                target_widget = btns.first()
        elif tab_id == "tab_crawler":
            inps = self.query("#input_crawler_url")
            if inps:
                target_widget = inps.first()
        elif tab_id == "tab_tookie":
            inps = self.query("#input_tookie_user")
            if inps:
                target_widget = inps.first()
        elif tab_id == "tab_arsenal":
            tables = self.query("#arsenal_table")
            if tables:
                target_widget = tables.first()
        elif tab_id == "tab_tailscale":
            tables = self.query("#devices_table")
            if tables:
                target_widget = tables.first()
        elif tab_id == "tab_uro":
            btns = self.query("#btn_run_uro")
            if btns:
                target_widget = btns.first()
        elif tab_id == "tab_legba":
            inps = self.query("#input_legba_user")
            if inps:
                target_widget = inps.first()

        if target_widget:
            target_widget.focus()
            self.call_after_refresh(target_widget.focus)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        active_id = event.tabbed_content.active
        self._focus_tab_widget(active_id)
        if active_id == "tab_arsenal":
            self._update_arsenal_preview()
        elif active_id == "tab_legba":
            self._update_legba_preview()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        inp_id = event.input.id
        if inp_id == "input_crawler_url":
            self._handle_crawler_run()
        elif inp_id == "input_tookie_user":
            self._handle_tookie_run()
        elif inp_id in ("input_arsenal_query", "input_arsenal_port"):
            self._populate_arsenal()
        elif inp_id == "input_arsenal_set_var":
            self._handle_set_arsenal_var()
        elif inp_id == "term_input":
            self._send_pty_input()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table_id = event.data_table.id
        if table_id == "arsenal_table":
            self._execute_selected_arsenal()
        elif table_id == "devices_table":
            dt = event.data_table
            if dt.row_count > 0:
                row_key, _ = dt.coordinate_to_cell_key(dt.cursor_coordinate)
                target = self.engine.get_target(str(row_key.value))
                if target:
                    self.active_target = target
                    self.notify(f"Active target locked: {target.name} ({target.tailscale_ip})")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "arsenal_table":
            self._update_arsenal_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_home_crawl":
            self.action_switch_tab("tab_crawler")
        elif btn_id == "btn_home_tookie":
            self.action_switch_tab("tab_tookie")
        elif btn_id == "btn_home_arsenal":
            self.action_switch_tab("tab_arsenal")
        elif btn_id == "btn_home_mesh":
            self.action_switch_tab("tab_tailscale")
        elif btn_id == "btn_refresh_ts":
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
        elif btn_id in ("btn_sim_node", "btn_arsenal_sim_node"):
            sim = Target(name="lab-vulnerable-server", tailscale_ip="100.64.0.50", is_authorized_lab=True, os="linux")
            self.engine.register_target(sim)
            self.active_target = sim
            self.action_refresh_tailscale()
            self._log_terminal("[bold green][✓] Registered & selected simulated lab target: lab-vulnerable-server (100.64.0.50) [AUTHORIZED LAB][/bold green]")
            self.notify("Simulated authorized lab node registered.")
        elif btn_id == "btn_run_crawler":
            self._handle_crawler_run()
        elif btn_id == "btn_crawler_to_uro":
            self._handle_crawler_to_uro()
        elif btn_id == "btn_crawler_pipe_uro":
            self._handle_crawler_pipe_uro()
        elif btn_id == "btn_run_tookie":
            self._handle_tookie_run()
        elif btn_id == "btn_tookie_to_uro":
            self._handle_tookie_to_uro()
        elif btn_id == "btn_run_uro":
            self._handle_uro_run()
        elif btn_id == "btn_search_arsenal":
            self._populate_arsenal()
        elif btn_id == "btn_arsenal_set_var":
            self._handle_set_arsenal_var()
        elif btn_id == "btn_exec_arsenal":
            self._execute_selected_arsenal()
        elif btn_id == "btn_exec_legba":
            self._execute_legba()
        elif btn_id == "btn_send_pty":
            self._send_pty_input()
        elif btn_id == "btn_clear_pty":
            self.query_one("#term_log", RichLog).clear()

    # ==================== WEB CRAWLER HANDLERS ====================
    def _handle_crawler_run(self) -> None:
        inps = self.query("#input_crawler_url")
        if not inps:
            return
        target_url = inps.first().value.strip()
        if not target_url:
            if self.active_target:
                target_url = f"http://{self.active_target.tailscale_ip}:80"
                inps.first().value = target_url
            else:
                self.notify("Please enter a target URL to crawl.", severity="warning")
                return

        max_inps = self.query("#input_crawler_max_pages")
        max_p = 15
        if max_inps and max_inps.first().value.strip():
            try:
                max_p = int(max_inps.first().value.strip())
            except ValueError:
                max_p = 15

        self._run_crawler_worker(target_url, max_p)

    @work(exclusive=True, thread=True)
    def _run_crawler_worker(self, target_url: str, max_pages: int, auto_pipe_uro: bool = False) -> None:
        self.app.call_from_thread(
            self._log_terminal,
            f"\n[bold cyan][*] Running Web Crawler for: '{target_url}' (max pages: {max_pages})...[/bold cyan]",
        )
        self.app.call_from_thread(self.notify, f"Crawling {target_url}...")
        try:
            col = self.engine.run_crawler(target_url, max_pages=max_pages)
            self._last_collection = col

            def update_ui():
                dt_list = self.query("#crawler_results_table")
                if dt_list:
                    dt = dt_list.first()
                    dt.clear()
                    pages = col.metadata.get("pages", [])
                    for p in pages:
                        dt.add_row(p.get("url", ""), str(p.get("depth", 0)), "Page", str(p.get("status", 200)))
                    endpoints = col.metadata.get("endpoints", [])
                    for ep in endpoints:
                        dt.add_row(ep, "N/A", "API / Form Endpoint", "Discovered")

                self._log_terminal(
                    f"[bold green][+] Web Crawler finished: {col.count()} endpoints discovered from '{target_url}'.[/bold green]"
                )
                self.notify(f"Discovered {col.count()} endpoints. Send to Uro to normalize.")

            self.app.call_from_thread(update_ui)

            if auto_pipe_uro and col.items:
                self.app.call_from_thread(self._handle_uro_run)

        except Exception as e:
            def report_err():
                self._log_terminal(f"[bold red][-] Web Crawler error: {e}[/bold red]")
                self.notify(f"Web Crawler error: {e}", severity="error")
            self.app.call_from_thread(report_err)

    def _handle_crawler_to_uro(self) -> None:
        if not self._last_collection or not self._last_collection.items:
            self.notify("No crawl results to process. Run crawler first.", severity="warning")
            return
        self.action_switch_tab("tab_uro")
        self._handle_uro_run()

    def _handle_crawler_pipe_uro(self) -> None:
        inps = self.query("#input_crawler_url")
        if not inps:
            return
        target_url = inps.first().value.strip()
        if not target_url:
            if self.active_target:
                target_url = f"http://{self.active_target.tailscale_ip}:80"
                inps.first().value = target_url
            else:
                self.notify("Please enter a target URL.", severity="warning")
                return
        self._run_crawler_worker(target_url, 15, auto_pipe_uro=True)

    # ==================== TOOKIE HANDLERS ====================
    def _handle_tookie_run(self) -> None:
        inps = self.query("#input_tookie_user")
        if not inps:
            return
        user = inps.first().value.strip()
        if not user:
            self.notify("Please enter a username to discover.", severity="warning")
            return
        max_inps = self.query("#input_tookie_limit")
        max_urls = 50
        if max_inps and max_inps.first().value.strip():
            try:
                max_urls = int(max_inps.first().value.strip())
            except ValueError:
                max_urls = 50
        self._run_tookie_worker(user, max_results=max_urls)

    @work(exclusive=True, thread=True)
    def _run_tookie_worker(self, user: str, max_results: int = 50) -> None:
        self.app.call_from_thread(
            self._log_terminal,
            f"\n[bold #10b981][*] Running Tookie OSINT discovery for username: '{user}' (limit: {max_results} URLs)...[/bold #10b981]",
        )
        self.app.call_from_thread(
            self._log_terminal,
            "[dim][*] Querying public platforms & social profiles (please wait)...[/dim]",
        )
        self.app.call_from_thread(self.notify, f"Running Tookie discovery for '{user}'...")
        try:
            col = self.engine.run_tookie(user, max_results=max_results, timeout=60)
            self._last_collection = col

            def update_ui():
                dt_list = self.query("#tookie_results_table")
                if dt_list:
                    dt = dt_list.first()
                    dt.clear()
                    matches = col.metadata.get("matches", [])
                    for m in matches:
                        dt.add_row(m.get("platform", "Web"), m.get("url", ""), m.get("status", "possible match"))

                if col.metadata.get("warning"):
                    self._log_terminal(f"[bold yellow][!] {col.metadata['warning']}[/bold yellow]")

                # Auto-populate Legba username field with discovered handle
                legba_users = self.query("#input_legba_user")
                if legba_users and user:
                    legba_users.first().value = user

                # Auto-populate Arsenal-NG session variables
                if user:
                    self.engine.set_session_variable("user", user)
                    self.engine.set_session_variable("username", user)
                    self._update_arsenal_preview()

                self._log_terminal(
                    f"[bold green][+] Tookie finished: {col.count()} URLs discovered for '{user}'.[/bold green]"
                )
                self.notify(f"Tookie found {col.count()} URLs! Click 'Send to Uro' to filter.")

            self.app.call_from_thread(update_ui)
        except Exception as e:
            def report_err():
                self._log_terminal(f"[bold red][-] Tookie error: {e}[/bold red]")
                self.notify(f"Tookie error: {e}", severity="error")
            self.app.call_from_thread(report_err)

    def _handle_tookie_to_uro(self) -> None:
        if not self._last_collection or not self._last_collection.items:
            self.notify("No Tookie results to process. Run discovery first.", severity="warning")
            return
        self.action_switch_tab("tab_uro")
        self._handle_uro_run()

    # ==================== URO HANDLERS ====================
    def _handle_uro_run(self) -> None:
        if not self._last_collection or not self._last_collection.items:
            # Check if there is active target with IP
            if self.active_target:
                fallback_urls = [
                    f"http://{self.active_target.tailscale_ip}:80/index.html",
                    f"http://{self.active_target.tailscale_ip}:80/login.php?user=1",
                    f"http://{self.active_target.tailscale_ip}:80/login.php?user=2",
                    f"http://{self.active_target.tailscale_ip}:80/static/style.css",
                    f"http://{self.active_target.tailscale_ip}:80/static/logo.png",
                ]
                self._last_collection = URLCollection(items=fallback_urls, source_tool="manual_target")
                self._log_terminal(f"[*] Pre-populated test URLs for target: {self.active_target.tailscale_ip}")
            else:
                self.notify("No URL collection loaded. Run Web Crawler or Tookie first.", severity="warning")
                return

        self._run_uro_worker(self._last_collection)

    @work(exclusive=True, thread=True)
    def _run_uro_worker(self, col: URLCollection) -> None:
        self.app.call_from_thread(
            self._log_terminal,
            f"\n[bold yellow][*] Running Uro URL filter pipeline on {col.count()} raw items...[/bold yellow]",
        )
        try:
            filtered = self.engine.run_uro(col)

            def update_ui():
                dt_list = self.query("#uro_results_table")
                lbl_list = self.query("#uro_status_label")
                if dt_list:
                    dt = dt_list.first()
                    dt.clear()
                    for item in filtered.items:
                        dt.add_row(item)

                if lbl_list:
                    status_text = (
                        f"Cleaned {col.count()} raw URLs down to {filtered.count()} unique endpoints "
                        f"(Efficiency: {100 - int(filtered.count()/max(col.count(),1)*100)}% noise eliminated)"
                    )
                    lbl_list.first().update(f"[bold green]✓ {status_text}[/bold green]")

                self._log_terminal(
                    f"[bold green][✓] Uro complete: Retained {filtered.count()}/{col.count()} distinct actionable URLs.[/bold green]"
                )
                self.notify(f"Uro pipeline reduced noise by {col.count() - filtered.count()} URLs!")

            self.app.call_from_thread(update_ui)
        except Exception as e:
            def report_err():
                self._log_terminal(f"[bold red][-] Uro error: {e}[/bold red]")
                self.notify(f"Uro filter error: {e}", severity="error")
            self.app.call_from_thread(report_err)

    # ==================== ARSENAL-NG HANDLERS ====================
    def _populate_arsenal(self) -> None:
        inps = self.query("#input_arsenal_query")
        query = inps.first().value.strip() if inps else ""

        cmds = self.engine.search_commands(query, limit=100)
        self._current_cmds = cmds

        dt_list = self.query("#arsenal_table")
        if not dt_list:
            return
        dt = dt_list.first()
        dt.clear()

        for c in cmds:
            lab_badge = "[bold red]YES[/bold red]" if c.requires_authorized_lab else "[green]NO[/green]"
            tool_name = getattr(c, "source_tool", "misc")
            cmd_tags = getattr(c, "tags", [])
            if cmd_tags:
                tags_str = ", ".join(cmd_tags)
                tool_display = f"[bold #10b981]{tool_name}[/bold #10b981]  [dim]\\[{escape(tags_str)}\\][/dim]"
            else:
                tool_display = f"[bold #10b981]{tool_name}[/bold #10b981]"
            dt.add_row(tool_display, c.title, lab_badge)

        self._update_arsenal_vars_display()
        if cmds:
            self._update_arsenal_preview()

    def _update_arsenal_vars_display(self) -> None:
        lbls = self.query("#arsenal_vars_status")
        if not lbls:
            return
        sess_vars = self.engine.get_session_variables()
        var_pairs = [f"{k}={v}" for k, v in list(sess_vars.items())[:6]]
        target_name = self.active_target.name if self.active_target else "None"
        lbls.first().update(f"Active Vars: {', '.join(var_pairs)} | Target: [bold #10b981]{target_name}[/bold #10b981]")

    def _update_arsenal_preview(self) -> None:
        previews = self.query("#arsenal_cmd_preview")
        descs = self.query("#arsenal_cmd_desc")
        dt_list = self.query("#arsenal_table")

        if not previews or not dt_list:
            return
        preview_widget = previews.first()
        desc_widget = descs.first() if descs else None
        dt = dt_list.first()

        if dt.row_count == 0 or not hasattr(self, "_current_cmds") or not self._current_cmds:
            preview_widget.update("$ [No command templates found]")
            if desc_widget:
                desc_widget.update("No command selected.")
            return

        row_idx = dt.cursor_row
        if row_idx is None or row_idx < 0:
            row_idx = 0

        if row_idx < len(self._current_cmds):
            cmd = self._current_cmds[row_idx]
            try:
                prep = self.engine.prepare_command(cmd, target=self.active_target)
                preview_widget.update(f"$ {prep.display_string}")
                if desc_widget:
                    tool_val = getattr(cmd, "source_tool", "misc")
                    cmd_tags = getattr(cmd, "tags", [])
                    tags_display = f"[{', '.join(cmd_tags)}]" if cmd_tags else "[]"
                    desc_text = (
                        f"Tool: {tool_val}  {tags_display}\n"
                        f"Action: {cmd.title}  |  Requires Lab: {cmd.requires_authorized_lab}\n"
                        f"{cmd.description}"
                    )
                    desc_widget.update(desc_text)
            except Exception as e:
                preview_widget.update(f"⛔ Error: {e}")
                if desc_widget:
                    desc_widget.update(f"Command requires parameters: {getattr(cmd, 'placeholders', {})}")

    def _handle_set_arsenal_var(self) -> None:
        inp = self.query_one("#input_arsenal_set_var", Input)
        val = inp.value.strip()
        if "=" in val:
            k, v = val.split("=", 1)
            self.engine.set_session_variable(k.strip(), v.strip())
            self.notify(f"Variable set: {k.strip()} = {v.strip()}")
            self._update_arsenal_vars_display()
        else:
            self.notify("Format must be key=val (e.g. port=8080)", severity="warning")
        inp.value = ""
        self._update_arsenal_preview()

    def _execute_selected_arsenal(self) -> None:
        dt_list = self.query("#arsenal_table")
        if not dt_list:
            return
        dt = dt_list.first()
        if dt.row_count == 0 or not hasattr(self, "_current_cmds") or not self._current_cmds:
            self.notify("No command templates available.", severity="warning")
            return

        row_idx = dt.cursor_row
        if row_idx is None or row_idx < 0:
            row_idx = 0

        if row_idx < len(self._current_cmds):
            cmd = self._current_cmds[row_idx]
            # Safety gate check
            if cmd.requires_authorized_lab:
                if not self.active_target or not self.active_target.is_authorized_lab:
                    target_name = self.active_target.name if self.active_target else "None"
                    err_msg = (
                        f"⛔ Safety Gate Blocked: Command '{cmd.title}' requires an authorized lab target. "
                        f"Target '{target_name}' is not authorized."
                    )
                    self._log_terminal(f"\n[bold red]{err_msg}[/bold red]")
                    self._log_terminal(
                        "[yellow]💡 Solution: Go to [2] Tailnet Mesh (press F3) and press Space to authorize a device, or click 'Simulate Lab Target'.[/yellow]"
                    )
                    self.notify(f"Safety Gate: Target '{target_name}' unauthorized.", severity="error")
                    return

            try:
                prep = self.engine.prepare_command(cmd, target=self.active_target)
                self.exec_mgr.send(self.session_id, prep)
                self._log_terminal(f"\n[bold green]$ {prep.display_string}[/bold green]")
                self.notify(f"▶ Dispatched '{prep.title}' to live PTY.")
            except Exception as e:
                self._log_terminal(f"\n[bold red]⛔ Command Preparation Error: {e}[/bold red]")
                self.notify(f"Safety Gate: {e}", severity="error")

    # ==================== LEGBA HANDLERS ====================
    def _update_legba_preview(self) -> None:
        previews = self.query("#legba_cmd_preview")
        if not previews:
            return
        preview_widget = previews.first()

        if not self.active_target:
            preview_widget.update("⛔ No active target selected. Go to [2] Tailnet Mesh.")
            return

        protos = self.query("#select_legba_proto")
        ports = self.query("#input_legba_port")
        users = self.query("#input_legba_user")
        pws = self.query("#input_legba_pass")

        proto = protos.first().value if (protos and protos.first().value) else "ssh"
        port_val = int(ports.first().value or 22) if ports else 22
        user_val = users.first().value if users else "admin"
        pw_val = pws.first().value if pws else "password123"

        try:
            cmd = self.engine.build_legba_command(
                protocol=str(proto),
                target=self.active_target,
                username=user_val,
                password=pw_val,
                port=port_val,
                concurrency=2,
            )
            preview_widget.update(f"$ {cmd.display_string}")
        except Exception as e:
            preview_widget.update(f"⛔ {e}")

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
            self._log_terminal(f"\n[bold red]$ {cmd.display_string}[/bold red]")
            self.notify(f"Dispatched Legba {proto.upper()} attack to persistent PTY.")
        except Exception as e:
            self._log_terminal(f"\n[bold red]⛔ Safety Gate Refused: {e}[/bold red]")
            self.notify(f"Safety Gate Refused Execution: {e}", severity="error")

    def _send_pty_input(self) -> None:
        inp = self.query_one("#term_input", Input)
        val = inp.value.strip()
        if val:
            # Check for Arsenal-NG interactive commands (set/unset/variables/tools)
            if self.engine.arsenal and (val.startswith("set ") or val.startswith("unset ") or val.lower() in ("variables", "vars", "tools")):
                resp = self.engine.arsenal.handle_command(val)
                if resp:
                    self._log_terminal(f"\n{resp}")
                    self._update_arsenal_preview()
                    inp.value = ""
                    return

            self.exec_mgr.send(self.session_id, val)
            self.query_one("#term_log", RichLog).write(f"$ {val}")
            inp.value = ""


def run_tui():
    """Entry point for the TUI."""
    app = TTULATUIApp()
    app.run()


if __name__ == "__main__":
    run_tui()

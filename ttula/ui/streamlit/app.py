"""Web Crawler - Operator Security Reconnaissance Console.

A unified security reconnaissance workspace for web crawling, identity discovery,
URL processing, OSINT workflows, and security command knowledge.
Follows Arsenal-style information architecture with centralized tool metadata
and restrained semantic accents.
"""

import os
import sys
import time
from typing import Optional
import streamlit as st

# Ensure ttula is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from ttula.config.tools import TOOLS, get_tool_metadata
from ttula.core.engine import TTULAEngine, create_default_engine
from ttula.core.models import Command, Target, URLCollection
from ttula.execution.manager import get_execution_manager
from ttula.ui.components.header import render_tool_header
from ttula.ui.components.home import render_home_page

# Page configuration
st.set_page_config(
    page_title="Web Crawler",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark, Modern Cybersecurity Palette (Section 7 of implementation.md)
# Background: #0B0F14 | Surface 1: #111820 | Surface 2: #17212B | Border: #27323D
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, pre, .terminal-text {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Base Theme Overrides */
    .stApp {
        background-color: #0B0F14;
        color: #F1F5F9;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111820 !important;
        border-right: 1px solid #27323D !important;
    }

    .sidebar-brand-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-brand-subtitle {
        color: #94A3B8;
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 500;
        margin-bottom: 1.25rem;
    }

    /* Cards and Surfaces */
    .card-surface {
        background: #111820;
        border: 1px solid #27323D;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .card-surface-interactive {
        background: #17212B;
        border: 1px solid #27323D;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s ease;
    }
    .card-surface-interactive:hover {
        border-color: #384A5C;
    }

    /* Lab Status Badges */
    .badge-authorized {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-unauthorized {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Terminal Console Display */
    .terminal-container {
        background: #070B0E;
        border: 1px solid #27323D;
        border-radius: 8px;
        padding: 14px;
        color: #38BDF8;
        font-size: 0.88rem;
        min-height: 280px;
        max-height: 420px;
        overflow-y: auto;
        white-space: pre-wrap;
    }

    /* Command Preview Box */
    .cmd-preview-box {
        background: #070B0E;
        border-left: 3px solid #00F0FF;
        border-top: 1px solid #27323D;
        border-right: 1px solid #27323D;
        border-bottom: 1px solid #27323D;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        color: #00F0FF;
        font-size: 0.90rem;
        margin: 10px 0;
    }

    /* Button and Input Styling */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        border-color: #00F0FF;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize Singleton Engine & Persistent Session
@st.cache_resource
def get_engine() -> TTULAEngine:
    return create_default_engine(mock_tailscale=False, force_native_uro=False)


engine = get_engine()
exec_mgr = get_execution_manager()

# Ensure session state maintains persistent PTY ID across reruns
if "active_session_id" not in st.session_state:
    node = engine.get_default_execution_node()
    sess = exec_mgr.create_session(node, session_id="ttula_main_pty")
    st.session_state["active_session_id"] = sess.id
    st.session_state["active_session_node"] = node.name

if "terminal_log" not in st.session_state:
    st.session_state["terminal_log"] = "[*] Web Crawler Interactive PTY initialized. Ready for operations.\n"

if "last_url_collection" not in st.session_state:
    st.session_state["last_url_collection"] = None

# Navigation state sync
NAV_OPTIONS = [
    "⌂ Home",
    "🕸️ Web Crawler",
    "🔍 Tookie (OSINT)",
    "🧹 Uro (URL Processing)",
    "📚 Arsenal-NG",
    "🔐 Legba (Auth)",
    "🌐 Tailscale Mesh",
    "💻 Live Terminal",
]

if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = NAV_OPTIONS[0]

# Read any fresh output from the persistent PTY session
try:
    fresh_output = exec_mgr.read(st.session_state["active_session_id"], timeout=0.05)
    if fresh_output:
        st.session_state["terminal_log"] += fresh_output
except Exception:
    pass


# Sidebar Header & Navigation
with st.sidebar:
    st.markdown('<div class="sidebar-brand-title">🕸️ WEB CRAWLER</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-brand-subtitle">Security Reconnaissance Workspace</div>', unsafe_allow_html=True)

    # Active Execution Node & Session Status
    st.markdown('<div style="border-top: 1px solid #27323D; margin-bottom: 12px;"></div>', unsafe_allow_html=True)
    sess_id = st.session_state["active_session_id"]
    sess_obj = exec_mgr.get_session(sess_id)
    cmd_count = exec_mgr.get_command_count(sess_id)

    status_color = "🟢" if (sess_obj and sess_obj.alive) else "🔴"
    st.caption(f"{status_color} **PTY Session**: `{sess_id}`")
    st.caption(f"⚡ **Commands Executed**: `{cmd_count}` | **Node**: `{st.session_state['active_session_node']}`")

    if st.button("🔄 Reset PTY Session", use_container_width=True):
        exec_mgr.kill(sess_id)
        new_sess = exec_mgr.create_session(engine.get_default_execution_node(), session_id="ttula_main_pty")
        st.session_state["active_session_id"] = new_sess.id
        st.session_state["terminal_log"] = "[*] PTY Session restarted.\n"
        st.rerun()

    st.markdown('<div style="border-top: 1px solid #27323D; margin: 12px 0;"></div>', unsafe_allow_html=True)

    # Find index of current nav_selection safely
    current_index = 0
    if st.session_state["nav_selection"] in NAV_OPTIONS:
        current_index = NAV_OPTIONS.index(st.session_state["nav_selection"])

    selected_menu = st.radio(
        "Navigation",
        NAV_OPTIONS,
        index=current_index,
        label_visibility="collapsed",
    )
    st.session_state["nav_selection"] = selected_menu


menu = st.session_state["nav_selection"]

# ==============================================================================
# VIEW 0: HOME PAGE
# ==============================================================================
if menu == "⌂ Home":
    render_home_page()


# ==============================================================================
# VIEW 1: WEB CRAWLER
# ==============================================================================
elif menu == "🕸️ Web Crawler":
    render_tool_header("web_crawler")

    with st.container():
        st.markdown('<div class="card-surface">', unsafe_allow_html=True)
        col_url, col_pages = st.columns([3, 1])

        # Pre-fill URL if active lab target is selected in session variables
        default_target_url = "http://100.64.0.50"
        if engine.arsenal:
            var_url = engine.arsenal.get_variable("url")
            if var_url:
                default_target_url = var_url

        with col_url:
            target_url = st.text_input("Target Web Service URL", value=default_target_url, placeholder="http://100.x.x.x:8080 or https://target.lab")
        with col_pages:
            max_pages = st.slider("Crawl Depth / Max Pages", min_value=1, max_value=50, value=15)

        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            crawl_btn = st.button("🚀 Start Web Crawl", type="primary", use_container_width=True)

        if crawl_btn:
            if not target_url.strip():
                st.error("Please provide a valid Target URL.")
            else:
                with st.spinner(f"Crawling {target_url.strip()} (up to {max_pages} pages)..."):
                    try:
                        collection = engine.run_crawler(target_url.strip(), max_pages=max_pages)
                        st.session_state["last_url_collection"] = collection
                        st.success(f"Crawl finished: Discovered {collection.count()} endpoints.")
                    except Exception as e:
                        st.error(f"Crawler error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    active_col = st.session_state.get("last_url_collection")
    if active_col and hasattr(active_col, "items") and active_col.items:
        st.markdown(f"### Discovered Web Endpoints ({active_col.count()} items)")

        col_act1, col_act2 = st.columns([1.5, 4])
        with col_act1:
            if st.button("🧹 Send Endpoints to Uro for Normalization", type="primary", use_container_width=True):
                cleaned = engine.run_uro(active_col)
                st.session_state["last_url_collection"] = cleaned
                st.session_state["nav_selection"] = "🧹 Uro (URL Processing)"
                st.success(f"Discovered endpoints piped to Uro: {active_col.count()} → {cleaned.count()}")
                st.rerun()

        st.code("\n".join(active_col.items), language="text")


# ==============================================================================
# VIEW 2: TOOKIE OSINT
# ==============================================================================
elif menu == "🔍 Tookie (OSINT)":
    render_tool_header("tookie")

    with st.container():
        st.markdown('<div class="card-surface">', unsafe_allow_html=True)
        with st.form("tookie_form"):
            username = st.text_input("Target Username / Persona Handle", placeholder="e.g. labuser or testoperator")
            timeout = st.slider("Query Timeout (seconds)", min_value=10, max_value=120, value=45)
            submitted = st.form_submit_button("🚀 Run Tookie Discovery", type="primary")

        if submitted:
            if not username.strip():
                st.error("Please specify a valid username.")
            else:
                with st.spinner(f"Querying 500+ web platforms for '{username}'..."):
                    try:
                        collection = engine.run_tookie(username.strip(), timeout=timeout)
                        st.session_state["last_url_collection"] = collection
                        # Auto-update Arsenal-NG session variables
                        if engine.arsenal:
                            engine.arsenal.set_variable("user", username.strip())
                            engine.arsenal.set_variable("username", username.strip())
                        st.success(f"Discovery complete. Discovered {collection.count()} public account profiles.")
                    except Exception as e:
                        st.error(f"Tookie error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    active_col = st.session_state.get("last_url_collection")
    if active_col and hasattr(active_col, "items") and active_col.items:
        st.markdown(f"### Discovered URLs ({active_col.count()} items)")
        disclaimer = active_col.metadata.get("disclaimer") if hasattr(active_col, "metadata") else None
        if disclaimer:
            st.warning(f"⚠️ **OSINT Safety Notice**: {disclaimer}")

        col_u1, col_u2 = st.columns([1.5, 4])
        with col_u1:
            if st.button("🧹 Pipe Collection to Uro for Deduplication", type="primary", use_container_width=True):
                cleaned = engine.run_uro(active_col)
                st.session_state["last_url_collection"] = cleaned
                st.session_state["nav_selection"] = "🧹 Uro (URL Processing)"
                st.success(f"Pipeline executed! URLs cleaned: {active_col.count()} → {cleaned.count()}")
                st.rerun()

        matches = active_col.metadata.get("matches", []) if hasattr(active_col, "metadata") else []
        if matches:
            st.dataframe(matches, use_container_width=True)
        else:
            st.code("\n".join(active_col.items), language="text")


# ==============================================================================
# VIEW 3: URO URL PROCESSING
# ==============================================================================
elif menu == "🧹 Uro (URL Processing)":
    render_tool_header("uro")

    active_col = st.session_state.get("last_url_collection")
    default_text = "\n".join(active_col.items) if (active_col and hasattr(active_col, "items") and active_col.items) else ""

    with st.container():
        st.markdown('<div class="card-surface">', unsafe_allow_html=True)
        custom_urls = st.text_area(
            "Input URLs (one per line, populated from Web Crawler or Tookie)",
            value=default_text,
            height=220,
            placeholder="https://example.lab/page?id=1\nhttps://example.lab/page?id=2",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            run_uro_btn = st.button("⚡ Clean & Deduplicate with Uro", type="primary", use_container_width=True)

        if run_uro_btn:
            lines = [u.strip() for u in custom_urls.splitlines() if u.strip()]
            if not lines:
                st.error("No URLs provided to normalize.")
            else:
                with st.spinner("Processing with Uro..."):
                    input_col = URLCollection(items=lines, source_tool="manual_or_pipeline")
                    cleaned_col = engine.run_uro(input_col)
                    st.session_state["last_url_collection"] = cleaned_col
                    st.success(f"Uro completed: {len(lines)} original endpoints reduced to {cleaned_col.count()} clean endpoints.")
        st.markdown('</div>', unsafe_allow_html=True)

    active_col = st.session_state.get("last_url_collection")
    if active_col and hasattr(active_col, "source_tool") and active_col.source_tool == "uro":
        st.markdown(f"### Cleaned Endpoint Inventory ({active_col.count()} unique)")
        st.code("\n".join(active_col.items), language="text")


# ==============================================================================
# VIEW 4: ARSENAL-NG
# ==============================================================================
elif menu == "📚 Arsenal-NG":
    render_tool_header("arsenal")

    # Global Session Variables Display Bar
    if engine.arsenal:
        st.markdown('<div class="card-surface" style="padding: 10px 16px;">', unsafe_allow_html=True)
        v = engine.get_session_variables()
        var_items = [f"**{k}**: `{v.get(k) or '(unset)'}`" for k in ("ip", "port", "user", "url", "domain")]
        st.markdown("⚡ **Active Session Variables:** " + " &nbsp;|&nbsp; ".join(var_items))
        st.markdown('</div>', unsafe_allow_html=True)

    col_q, col_cat = st.columns([3, 2])
    with col_q:
        search_query = st.text_input("Search 247+ tools & 2,900+ playbooks", placeholder="e.g. nmap, curl, impacket, syn, smb, fuzz...")
    with col_cat:
        available_cats = ["All Categories"] + (engine.arsenal.list_categories() if engine.arsenal else [])
        selected_cat = st.selectbox("Category Filter", available_cats)

    query = search_query if search_query else ("" if selected_cat == "All Categories" else selected_cat)
    candidate_cmds = engine.find_commands(query)

    st.markdown(f"Found **{len(candidate_cmds)}** matching playbooks.")

    # Target selection for placeholder filling
    all_targets = engine.list_targets()
    target_options = {f"{t.name} ({t.tailscale_ip}){' [AUTHORIZED LAB]' if t.is_authorized_lab else ' [UNAUTHORIZED]'}": t for t in all_targets}
    chosen_label = st.selectbox("Active Target Context:", list(target_options.keys()) if target_options else ["No targets available"])
    chosen_target = target_options.get(chosen_label) if target_options else None

    # Sync selected target with session variables
    if chosen_target and engine.arsenal:
        engine.set_session_variable("target", chosen_target.tailscale_ip)
        engine.set_session_variable("ip", chosen_target.tailscale_ip)

    for i, cmd in enumerate(candidate_cmds[:150]):
        with st.container():
            st.markdown('<div class="card-surface-interactive">', unsafe_allow_html=True)
            col_t_title, col_t_badge = st.columns([4, 1])
            with col_t_title:
                st.markdown(f"#### {cmd.title}")
            with col_t_badge:
                if cmd.requires_authorized_lab:
                    st.markdown('<span class="badge-unauthorized" style="float: right;">LAB REQUIRED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-authorized" style="float: right;">PASSIVE / SAFE</span>', unsafe_allow_html=True)

            st.caption(f"Tool: `{cmd.source_tool}` • {cmd.description}")

            try:
                prepared = engine.prepare_command(cmd, target=chosen_target)
                can_run = True
                err_msg = ""
            except Exception as e:
                prepared = cmd
                can_run = False
                err_msg = str(e)

            st.markdown(f'<div class="cmd-preview-box">$ {prepared.display_string}</div>', unsafe_allow_html=True)

            if not can_run:
                st.error(f"⛔ Safety Gate: {err_msg}")
            else:
                col_ex1, col_ex2 = st.columns([2, 5])
                with col_ex1:
                    if st.button("▶ Execute in PTY Terminal", key=f"run_pty_{i}", type="primary"):
                        exec_mgr.send(st.session_state["active_session_id"], prepared)
                        st.session_state["terminal_log"] += f"\n$ {prepared.display_string}\n"
                        st.success("Dispatched to persistent terminal session!")
            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# VIEW 5: LEGBA AUTH
# ==============================================================================
elif menu == "🔐 Legba (Auth)":
    render_tool_header("legba")

    for w in engine.legba.get_safety_warnings() if engine.legba else []:
        st.warning(f"⚠️ {w}")

    auth_targets = engine.get_authorized_lab_targets()
    if not auth_targets:
        st.error("⛔ NO AUTHORIZED LAB TARGETS FOUND! Legba requires an explicitly authorized lab target.")
        st.info("Navigate to '🌐 Tailscale Mesh' to authorize your lab server first.")
    else:
        target_map = {f"{t.name} ({t.tailscale_ip})": t for t in auth_targets}
        selected_t_name = st.selectbox("Select Authorized Lab Target", list(target_map.keys()))
        selected_target = target_map[selected_t_name]

        protocols = engine.legba.get_supported_protocols() if engine.legba else ["ssh", "http", "smb", "ftp"]
        c_proto, c_port, c_conc = st.columns(3)
        with c_proto:
            proto = st.selectbox("Protocol", protocols, index=0)
        with c_port:
            port_input = st.number_input("Port (0 = default)", min_value=0, max_value=65535, value=22 if proto == "ssh" else 80)
        with c_conc:
            concurrency = st.slider("Concurrency (-c)", min_value=1, max_value=10, value=2)

        c_u, c_p = st.columns(2)
        with c_u:
            user_mode = st.radio("Username Mode", ["Single Username", "User Wordlist"])
            if user_mode == "Single Username":
                username_val = st.text_input("Username", value="admin")
                user_wl = ""
            else:
                user_wl = st.text_input("User Wordlist Path", value="/usr/share/wordlists/seclists/Usernames/top-usernames-shortlist.txt")
                username_val = ""
        with c_p:
            pass_mode = st.radio("Password Mode", ["Single Password", "Password Wordlist"])
            if pass_mode == "Single Password":
                pass_val = st.text_input("Password", value="password123", type="password")
                pass_wl = ""
            else:
                pass_wl = st.text_input("Password Wordlist Path", value="/usr/share/wordlists/fasttrack.txt")
                pass_val = ""

        try:
            legba_cmd = engine.build_legba_command(
                protocol=proto,
                target=selected_target,
                username=username_val,
                password=pass_val,
                wordlist_user=user_wl,
                wordlist_pass=pass_wl,
                port=port_input if port_input > 0 else None,
                concurrency=concurrency,
            )

            st.markdown("### 🔍 Verified Command Preview Before Execution:")
            st.markdown(f'<div class="cmd-preview-box">$ {legba_cmd.display_string}</div>', unsafe_allow_html=True)
            st.caption(f"Target is verified: **{selected_target.name}** ({selected_target.tailscale_ip}) [AUTHORIZED]")

            if st.button("🚀 Launch Legba Authentication Test in PTY", type="primary"):
                exec_mgr.send(st.session_state["active_session_id"], legba_cmd)
                st.session_state["terminal_log"] += f"\n$ {legba_cmd.display_string}\n"
                st.success("Legba test dispatched to persistent PTY session!")
        except Exception as e:
            st.error(f"Could not build command: {e}")


# ==============================================================================
# VIEW 6: TAILSCALE MESH
# ==============================================================================
elif menu == "🌐 Tailscale Mesh":
    render_tool_header("tailscale")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 Refresh Mesh Status"):
            st.rerun()

    status_data = engine.get_tailscale_status()
    is_online = status_data.get("online", False)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tailscale Mesh Daemon", "ONLINE" if is_online else "STANDALONE / OFFLINE", delta="Ready" if is_online else "Local")
    col2.metric("Local Node IP", status_data.get("self_ip", "127.0.0.1"))
    col3.metric("Tailnet Devices", status_data.get("device_count", 0))

    st.markdown("### Discovered Lab Mesh Devices")
    targets = engine.list_targets()

    if not targets:
        st.info("No remote peer devices detected. Tailscale may be offline or in single-node mode.")
        if st.button("Simulate Lab Target for Testing"):
            sim_target = Target(
                name="lab-vulnerable-server",
                tailscale_ip="100.64.0.50",
                is_authorized_lab=True,
                hostname="lab-server.tailnet",
            )
            engine.register_target(sim_target)
            st.success("Simulated lab target registered and authorized.")
            st.rerun()
    else:
        for target in targets:
            with st.container():
                st.markdown('<div class="card-surface">', unsafe_allow_html=True)
                c_name, c_ip, c_auth, c_action = st.columns([2.5, 2, 2, 2.5])
                with c_name:
                    st.markdown(f"**{target.name}**")
                    if target.hostname:
                        st.caption(f"Host: `{target.hostname}`")
                with c_ip:
                    st.markdown(f"`{target.tailscale_ip}`")
                    if target.os:
                        st.caption(f"OS: {target.os}")
                with c_auth:
                    if target.is_authorized_lab:
                        st.markdown('<span class="badge-authorized">✓ AUTHORIZED LAB</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-unauthorized">✗ RESTRICTED</span>', unsafe_allow_html=True)
                with c_action:
                    if target.is_authorized_lab:
                        if st.button("Revoke Authorization", key=f"revoke_{target.name}"):
                            engine.set_target_authorization(target.name, False)
                            st.rerun()
                    else:
                        if st.button("Authorize as Lab Target", key=f"auth_{target.name}", type="primary"):
                            engine.set_target_authorization(target.name, True)
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# VIEW 7: LIVE TERMINAL
# ==============================================================================
elif menu == "💻 Live Terminal":
    render_tool_header("terminal")

    new_data = exec_mgr.read(st.session_state["active_session_id"], timeout=0.2)
    if new_data:
        st.session_state["terminal_log"] += new_data

    st.markdown(
        f'<div class="terminal-container">{st.session_state["terminal_log"]}</div>',
        unsafe_allow_html=True,
    )

    with st.form("terminal_input_form", clear_on_submit=True):
        col_in, col_btn = st.columns([5, 1])
        with col_in:
            user_cmd = st.text_input("Send command to interactive PTY", placeholder="e.g. echo $USER or tailscale status or set ip=100.64.0.50", label_visibility="collapsed")
        with col_btn:
            send_btn = st.form_submit_button("Send ⏎", type="primary")

    if send_btn and user_cmd.strip():
        # Handle Arsenal-NG special commands
        cmd_str = user_cmd.strip()
        if engine.arsenal and (cmd_str.startswith("set ") or cmd_str.startswith("unset ") or cmd_str.lower() in ("variables", "vars", "tools")):
            resp = engine.arsenal.handle_command(cmd_str)
            if resp:
                st.session_state["terminal_log"] += f"\n$ {cmd_str}\n{resp}\n"
        else:
            exec_mgr.send(st.session_state["active_session_id"], cmd_str)
            st.session_state["terminal_log"] += f"\n$ {cmd_str}\n"

        time.sleep(0.15)
        fresh = exec_mgr.read(st.session_state["active_session_id"], timeout=0.3)
        if fresh:
            st.session_state["terminal_log"] += fresh
        st.rerun()

    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        if st.button("🧹 Clear Terminal Output"):
            st.session_state["terminal_log"] = "[*] Terminal cleared.\n"
            st.rerun()

"""TTULA Streamlit UI - Operator Security Operations Console.

Personal, Kali-native orchestration layer for authorized security lab workflows.
Follows TRD specification: pure control surface calling core.engine,
session persistence across reruns via ExecutionManager singleton,
and strict safety gates before command execution.
"""

import os
import sys
import time
from typing import Optional
import streamlit as st

# Ensure ttula is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from ttula.core.engine import TTULAEngine, create_default_engine
from ttula.core.models import Command, Target, URLCollection
from ttula.execution.manager import get_execution_manager

# Page configuration
st.set_page_config(
    page_title="TTULA // SecOps Orchestrator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Cyber Dark Glassmorphism Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    code, pre, .terminal-text {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Background & Main Layout */
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(at 10% 20%, rgba(0, 240, 255, 0.05) 0px, transparent 50%),
            radial-gradient(at 90% 80%, rgba(0, 255, 136, 0.04) 0px, transparent 50%);
        color: #e2e8f0;
    }

    /* Glowing Title */
    .app-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00f0ff 0%, #7000ff 50%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    .app-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 1.5rem;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(18, 24, 38, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Badges */
    .badge-authorized {
        background: rgba(0, 255, 136, 0.15);
        color: #00ff88;
        border: 1px solid rgba(0, 255, 136, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-unauthorized {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-status {
        background: rgba(0, 240, 255, 0.15);
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Terminal Console Display */
    .terminal-container {
        background: #06090e;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px;
        color: #38bdf8;
        font-size: 0.88rem;
        min-height: 280px;
        max-height: 420px;
        overflow-y: auto;
        white-space: pre-wrap;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.6);
    }

    /* Command Preview Box */
    .cmd-preview-box {
        background: #0f172a;
        border-left: 4px solid #00f0ff;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        color: #38bdf8;
        font-size: 0.9rem;
        margin: 10px 0;
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
    st.session_state["terminal_log"] = "[*] TTULA Interactive PTY initialized. Ready for operations.\n"

if "last_url_collection" not in st.session_state:
    st.session_state["last_url_collection"] = None


# Read any fresh output from the persistent PTY session
try:
    fresh_output = exec_mgr.read(st.session_state["active_session_id"], timeout=0.05)
    if fresh_output:
        st.session_state["terminal_log"] += fresh_output
except Exception:
    pass


# Sidebar Header & Navigation
with st.sidebar:
    st.markdown('<div class="app-title">TTULA</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Security Operations Orchestration</div>', unsafe_allow_html=True)

    # Active Execution Node & Session Status
    st.markdown("---")
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

    st.markdown("---")
    menu = st.radio(
        "Navigation",
        [
            "🌐 Network & Tailscale",
            "🔍 OSINT Discovery (Tookie)",
            "🧹 URL Processing (Uro)",
            "📚 Command Cheats (Arsenal)",
            "🔐 Auth Testing (Legba)",
            "💻 Live Terminal (PTY)",
        ],
        index=0,
    )


# --- VIEW 1: Network & Tailscale ---
if menu == "🌐 Network & Tailscale":
    st.subheader("Tailscale Network Mesh & Lab Target Inventory")
    st.caption("Inspect tailnet devices and explicitly authorize vulnerable lab targets for testing.")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 Refresh Status"):
            st.rerun()

    status_data = engine.get_tailscale_status()
    is_online = status_data.get("online", False)

    # Status summary banner
    col1, col2, col3 = st.columns(3)
    col1.metric("Tailscale Daemon", "ONLINE" if is_online else "OFFLINE", delta="Ready" if is_online else "Degraded")
    col2.metric("Local Node IP", status_data.get("self_ip", "127.0.0.1"))
    col3.metric("Tailnet Devices", status_data.get("device_count", 0))

    st.markdown("### Discovered Devices on Tailnet")
    targets = engine.list_targets()

    if not targets:
        st.info("No remote peer devices detected. Tailscale may be offline or in single-node mode.")
        if st.button("Simulate Lab Target for Testing"):
            sim_target = Target(
                name="lab-vulnerable-server",
                tailscale_ip="100.64.0.50",
                is_authorized_lab=False,
                hostname="lab-server.tailnet",
            )
            engine.register_target(sim_target)
            st.success("Simulated lab target registered.")
            st.rerun()
    else:
        for target in targets:
            with st.container():
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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


# --- VIEW 2: OSINT Discovery (Tookie) ---
elif menu == "🔍 OSINT Discovery (Tookie)":
    st.subheader("Tookie OSINT & Username Footprinting")
    st.caption("Perform automated reconnaissance against targets and extract candidate URLs.")

    with st.form("tookie_form"):
        username = st.text_input("Target Username / Handle", placeholder="e.g. labuser or testoperator")
        timeout = st.slider("Query Timeout (seconds)", min_value=10, max_value=120, value=45)
        submitted = st.form_submit_button("🚀 Run Tookie Discovery", type="primary")

    if submitted:
        if not username.strip():
            st.error("Please specify a valid username.")
        else:
            with st.spinner(f"Running Tookie against '{username}'..."):
                try:
                    collection = engine.run_tookie(username.strip(), timeout=timeout)
                    st.session_state["last_url_collection"] = collection
                    st.success(f"Discovery complete. Found {collection.count()} potential URLs/endpoints.")
                except Exception as e:
                    st.error(f"Tookie error: {e}")

    active_col = st.session_state.get("last_url_collection")
    if active_col and hasattr(active_col, "items") and active_col.items:
        st.markdown(f"### Discovered URLs ({active_col.count()} items)")
        disclaimer = active_col.metadata.get("disclaimer") if hasattr(active_col, "metadata") else None
        if disclaimer:
            st.warning(f"⚠️ **OSINT Safety Notice**: {disclaimer}")

        # One-click Send to Uro pipeline
        st.markdown("#### Direct Pipeline Action:")
        if st.button("🧹 Send Collection to Uro for Deduplication", type="primary"):
            cleaned = engine.run_uro(active_col)
            st.session_state["last_url_collection"] = cleaned
            st.success(f"Pipeline executed! URLs cleaned and deduplicated: {active_col.count()} → {cleaned.count()}")
            st.rerun()

        # Display matches table
        matches = active_col.metadata.get("matches", []) if hasattr(active_col, "metadata") else []
        if matches:
            st.dataframe(matches, use_container_width=True)
        else:
            st.code("\n".join(active_col.items), language="text")


# --- VIEW 3: URL Processing (Uro) ---
elif menu == "🧹 URL Processing (Uro)":
    st.subheader("Uro URL Filtering & Deduplication")
    st.caption("Clean, normalize, and eliminate redundant parameters from discovered URL lists.")

    active_col = st.session_state.get("last_url_collection")
    default_text = "\n".join(active_col.items) if (active_col and hasattr(active_col, "items") and active_col.items) else ""

    custom_urls = st.text_area(
        "Input URLs (One per line or loaded from Tookie)",
        value=default_text,
        height=220,
        placeholder="https://example.lab/page?id=1\nhttps://example.lab/page?id=2",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_uro_btn = st.button("⚡ Clean with Uro", type="primary")

    if run_uro_btn:
        lines = [u.strip() for u in custom_urls.splitlines() if u.strip()]
        if not lines:
            st.error("No URLs provided.")
        else:
            with st.spinner("Processing with Uro..."):
                input_col = URLCollection(items=lines, source_tool="manual_or_tookie")
                cleaned_col = engine.run_uro(input_col)
                st.session_state["last_url_collection"] = cleaned_col
                st.success(f"Uro finished: {len(lines)} original URLs reduced to {cleaned_col.count()} unique endpoints.")

    active_col = st.session_state.get("last_url_collection")
    if active_col and hasattr(active_col, "source_tool") and active_col.source_tool == "uro":
        st.markdown(f"### Cleaned Endpoint Inventory ({active_col.count()} unique)")
        st.code("\n".join(active_col.items), language="text")


# --- VIEW 4: Command Cheats (Arsenal) ---
elif menu == "📚 Command Cheats (Arsenal)":
    st.subheader("Arsenal-NG Command Knowledge Base")
    st.caption("Browse curated attack & enumeration playbooks with safe placeholder substitution.")

    col_q, col_cat = st.columns([3, 2])
    with col_q:
        search_query = st.text_input("Search playbooks (keyword, tag, tool)", placeholder="nmap, scan, web, ssh, smb...")
    with col_cat:
        available_cats = ["All Categories"] + (engine.arsenal.list_categories() if engine.arsenal else [])
        selected_cat = st.selectbox("Category Filter", available_cats)

    query = search_query if search_query else ("" if selected_cat == "All Categories" else selected_cat)
    candidate_cmds = engine.find_commands(query)

    st.markdown(f"Found **{len(candidate_cmds)}** candidate command templates.")

    # Target selection for placeholder filling
    auth_targets = engine.get_authorized_lab_targets()
    all_targets = engine.list_targets()

    target_options = {f"{t.name} ({t.tailscale_ip}){' [AUTHORIZED LAB]' if t.is_authorized_lab else ' [UNAUTHORIZED]'}": t for t in all_targets}
    chosen_label = st.selectbox("Select Target for Placeholder Filling:", list(target_options.keys()) if target_options else ["No targets available"])
    chosen_target = target_options.get(chosen_label) if target_options else None

    port_val = st.text_input("Port (optional)", value="80")
    wordlist_val = st.text_input("Wordlist path (optional)", value="/usr/share/wordlists/dirb/common.txt")

    for i, cmd in enumerate(candidate_cmds):
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"#### {cmd.title}")
            st.caption(f"Tool: `{cmd.source_tool}` | {cmd.description}")

            # Safe preparation
            try:
                prepared = engine.prepare_command(
                    cmd,
                    target=chosen_target,
                    extra_params={"port": port_val, "wordlist": wordlist_val},
                )
                can_run = True
                err_msg = ""
            except Exception as e:
                prepared = cmd
                can_run = False
                err_msg = str(e)

            # Command preview box
            st.markdown(f'<div class="cmd-preview-box">$ {prepared.display_string}</div>', unsafe_allow_html=True)

            if not can_run:
                st.error(f"⛔ {err_msg}")
            else:
                col_ex1, col_ex2 = st.columns([2, 5])
                with col_ex1:
                    # Execute in persistent PTY
                    if st.button(f"▶ Execute in PTY Terminal", key=f"run_pty_{i}", type="primary"):
                        exec_mgr.send(st.session_state["active_session_id"], prepared)
                        st.session_state["terminal_log"] += f"\n$ {prepared.display_string}\n"
                        st.success("Command dispatched to active PTY session! Switch to 'Live Terminal' to watch.")
            st.markdown('</div>', unsafe_allow_html=True)


# --- VIEW 5: Auth Testing (Legba) ---
elif menu == "🔐 Auth Testing (Legba)":
    st.subheader("Legba Authentication Testing")
    st.caption("Credential validation with strict lab authorization gating.")

    # Surface Legba Safety Warnings
    for w in engine.legba.get_safety_warnings() if engine.legba else []:
        st.warning(f"⚠️ {w}")

    auth_targets = engine.get_authorized_lab_targets()
    if not auth_targets:
        st.error("⛔ NO AUTHORIZED LAB TARGETS FOUND! Legba requires an explicitly authorized lab target.")
        st.info("Navigate to '🌐 Network & Tailscale' to authorize your lab server first.")
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

        # Build Legba Command Preview
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


# --- VIEW 6: Live Terminal (PTY) ---
elif menu == "💻 Live Terminal (PTY)":
    st.subheader("Persistent Interactive Terminal")
    st.caption("Direct PTY control session that survives UI reruns and streams output.")

    # Read latest output from PTY
    new_data = exec_mgr.read(st.session_state["active_session_id"], timeout=0.2)
    if new_data:
        st.session_state["terminal_log"] += new_data

    # Display terminal container
    st.markdown(
        f'<div class="terminal-container">{st.session_state["terminal_log"]}</div>',
        unsafe_allow_html=True,
    )

    # Command input form
    with st.form("terminal_input_form", clear_on_submit=True):
        col_in, col_btn = st.columns([5, 1])
        with col_in:
            user_cmd = st.text_input("Send command to shell", placeholder="echo 'Hello from TTULA' or tailscale netcheck", label_visibility="collapsed")
        with col_btn:
            send_btn = st.form_submit_button("Send ⏎", type="primary")

    if send_btn and user_cmd.strip():
        exec_mgr.send(st.session_state["active_session_id"], user_cmd.strip())
        st.session_state["terminal_log"] += f"\n$ {user_cmd.strip()}\n"
        time.sleep(0.15)
        fresh = exec_mgr.read(st.session_state["active_session_id"], timeout=0.3)
        if fresh:
            st.session_state["terminal_log"] += fresh
        st.rerun()

    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        if st.button("🧹 Clear Terminal Screen"):
            st.session_state["terminal_log"] = "[*] Terminal cleared.\n"
            st.rerun()

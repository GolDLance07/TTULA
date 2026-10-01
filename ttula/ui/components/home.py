"""Home Page Component for Web Crawler UI."""

import streamlit as st
from ttula.config.tools import TOOLS
from ttula.ui.components.badges import render_category_chips_html


def render_home_page(on_navigate=None) -> None:
    """Renders the comprehensive Home page for Web Crawler."""
    meta = TOOLS.get("home", {})

    home_hero_html = """
    <div style="
        background: #12171F;
        border: 1px solid #232D3B;
        border-radius: 12px;
        padding: 30px 34px;
        margin-bottom: 24px;
        position: relative;
    ">
        <div style="
            font-size: 2.1rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        ">
            🕸️ WEB CRAWLER
        </div>
        <div style="
            color: #94A3B8;
            font-size: 1.02rem;
            line-height: 1.65;
            max-width: 860px;
            margin-bottom: 18px;
        ">
            A unified security reconnaissance workspace engineered for rapid attack surface discovery,
            web spidering and endpoint extraction, digital persona OSINT footprinting, intelligent URL cleaning
            and parameter deduplication, automated execution across 190+ security tool cheat playbooks,
            and strict boundary-enforced lab credential testing through a zero-trust Tailscale mesh.
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span style="background: #18202C; border: 1px solid #283547; color: #10B981; padding: 3px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">RECONNAISSANCE</span>
            <span style="background: #18202C; border: 1px solid #283547; color: #A855F7; padding: 3px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">IDENTITY OSINT</span>
            <span style="background: #18202C; border: 1px solid #283547; color: #34D399; padding: 3px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">URL DE-NOISING</span>
            <span style="background: #18202C; border: 1px solid #283547; color: #F59E0B; padding: 3px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">190+ CHEAT PLAYBOOKS</span>
            <span style="background: #18202C; border: 1px solid #283547; color: #EF4444; padding: 3px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">LAB SAFETY GATED</span>
        </div>
    </div>
    """
    st.markdown(home_hero_html, unsafe_allow_html=True)

    # Primary Quick-Launch Buttons
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("🕸️ Start Web Crawl", use_container_width=True, type="primary"):
            st.session_state["nav_selection"] = "🕸️ Web Crawler"
            st.rerun()
    with col_b:
        if st.button("🔍 Identity OSINT", use_container_width=True):
            st.session_state["nav_selection"] = "🔍 Tookie (OSINT)"
            st.rerun()
    with col_c:
        if st.button("📚 Browse Tool Cheats", use_container_width=True):
            st.session_state["nav_selection"] = "📚 Arsenal-NG"
            st.rerun()
    with col_d:
        if st.button("🌐 Tailnet Mesh", use_container_width=True):
            st.session_state["nav_selection"] = "🌐 Tailscale Mesh"
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Steps to Use the Workspace (Short & Structured)
    steps_html = """
    <div style="
        background: #0E131A;
        border: 1px solid #232D3B;
        border-radius: 10px;
        padding: 22px 24px;
        margin-bottom: 24px;
    ">
        <div style="font-size: 1.15rem; font-weight: 700; color: #F1F5F9; margin-bottom: 14px;">
            📋 Workflow & Steps to Use
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
            <div style="background: #141A23; border: 1px solid #28323E; border-left: 3px solid #10B981; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #10B981; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 1 • Discover</div>
                <div style="color: #FFFFFF; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Endpoint & Persona Recon</div>
                <div style="color: #8E9DAE; font-size: 0.82rem; line-height: 1.45;">Crawl target web ports with <b>Web Crawler</b> or discover user accounts across 60+ platforms with <b>Tookie</b>.</div>
            </div>
            <div style="background: #141A23; border: 1px solid #28323E; border-left: 3px solid #F59E0B; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #F59E0B; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 2 • Clean</div>
                <div style="color: #FFFFFF; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Uro Normalization</div>
                <div style="color: #8E9DAE; font-size: 0.82rem; line-height: 1.45;">Pipe raw URL lists directly into <b>Uro</b> to strip static noise, tracking parameters, and duplicate endpoints.</div>
            </div>
            <div style="background: #141A23; border: 1px solid #28323E; border-left: 3px solid #34D399; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #34D399; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 3 • Select</div>
                <div style="color: #FFFFFF; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Tool Playbooks & Tags</div>
                <div style="color: #8E9DAE; font-size: 0.82rem; line-height: 1.45;">Search 190+ tool YAML cheats with side-by-side tags (Nmap, Impacket, FFUF) and automatic variable injection.</div>
            </div>
            <div style="background: #141A23; border: 1px solid #28323E; border-left: 3px solid #EF4444; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #EF4444; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 4 • Execute</div>
                <div style="color: #FFFFFF; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Safe PTY Dispatch</div>
                <div style="color: #8E9DAE; font-size: 0.82rem; line-height: 1.45;">Verify <b>Tailscale</b> authorized lab status and dispatch commands directly to the live, persistent <b>PTY Terminal</b>.</div>
            </div>
        </div>
    </div>
    """
    st.markdown(steps_html, unsafe_allow_html=True)

    # Integrated Tools Grid
    st.markdown("### Integrated Security Toolchain")
    grid_cols = st.columns(3)

    tool_items = [
        ("web_crawler", "🕸️ Web Crawler", "Deep endpoint discovery & link extraction for target web hosts."),
        ("tookie", "🔍 Tookie", "Multi-platform OSINT account profiling across 60+ web domains."),
        ("uro", "🧹 Uro", "High-efficiency URL normalization, parameter cleanup & noise removal."),
        ("arsenal", "📚 Arsenal-NG", "190+ tool cheatfiles & 2,900+ security actions with YAML tags."),
        ("legba", "🔐 Legba", "Fast multi-protocol authentication auditing for SSH, SMB, HTTP, and FTP."),
        ("tailscale", "🌐 Tailscale", "Zero-trust mesh network layer connecting authorized lab environments."),
    ]

    for i, (tool_id, display_title, short_desc) in enumerate(tool_items):
        tool_meta = TOOLS.get(tool_id, {})
        accent = tool_meta.get("accent", "#10B981")
        cats = tool_meta.get("categories", [])
        col = grid_cols[i % 3]

        with col:
            badges_html = render_category_chips_html(cats[:3])
            card_html = f"""
            <div style="
                background: #12171F;
                border: 1px solid #232D3B;
                border-top: 3px solid {accent};
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                min-height: 145px;
            ">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 0.98rem; margin-bottom: 4px;">
                    {display_title}
                </div>
                <div style="color: #8E9DAE; font-size: 0.84rem; line-height: 1.4; margin-bottom: 10px;">
                    {short_desc}
                </div>
                {badges_html}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    # Bottom Footer with Creator Credits positioned at the last in the side
    footer_html = """
    <div style="
        border-top: 1px solid #232D3B;
        margin-top: 36px;
        padding-top: 18px;
        padding-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    ">
        <div style="color: #64748B; font-size: 0.82rem;">
            Web Crawler • Security Reconnaissance Workspace
        </div>
        <div style="
            text-align: right;
            background: #141A23;
            border: 1px solid #28323E;
            border-right: 3px solid #10B981;
            border-radius: 6px;
            padding: 8px 16px;
        ">
            <span style="color: #64748B; font-size: 0.72rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Created by</span><br/>
            <span style="color: #E2E8F0; font-size: 0.90rem; font-weight: 600;">Aarush Rahul Patel &nbsp;·&nbsp; Shreya Singh</span>
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

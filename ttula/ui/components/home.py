"""Home Page Component for Web Crawler UI."""

import streamlit as st
from ttula.config.tools import TOOLS
from ttula.ui.components.badges import render_category_chips_html


def render_home_page(on_navigate=None) -> None:
    """Renders the comprehensive Home page for Web Crawler."""
    meta = TOOLS.get("home", {})

    home_hero_html = """
    <div style="
        background: #181818;
        border: 1px solid #3E3D32;
        border-radius: 10px;
        padding: 28px 32px;
        margin-bottom: 22px;
        position: relative;
    ">
        <div style="
            font-size: 2.1rem;
            font-weight: 800;
            color: #A6E22E;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            font-family: 'JetBrains Mono', monospace;
        ">
            🕸️ WEB CRAWLER
        </div>
        <div style="
            color: #F8F8F2;
            opacity: 0.9;
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
            <span style="background: #272822; border: 1px solid #3E3D32; color: #A6E22E; padding: 4px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">RECONNAISSANCE</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #FD971F; padding: 4px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">IDENTITY OSINT</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #E6DB74; padding: 4px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">URL DE-NOISING</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #AE81FF; padding: 4px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">190+ CHEAT PLAYBOOKS</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #F92672; padding: 4px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">LAB SAFETY GATED</span>
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

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Steps to Use the Workspace (Short & Structured)
    steps_html = """
    <div style="
        background: #181818;
        border: 1px solid #3E3D32;
        border-radius: 10px;
        padding: 22px 24px;
        margin-bottom: 14px;
    ">
        <div style="font-size: 1.15rem; font-weight: 700; color: #A6E22E; margin-bottom: 14px; font-family: 'JetBrains Mono', monospace;">
            📋 Workflow & Steps to Use
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #A6E22E; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #A6E22E; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 1 • Discover</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Endpoint & Persona Recon</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Crawl target web ports with <b>Web Crawler</b> or discover user accounts across 60+ platforms with <b>Tookie</b>.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #FD971F; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #FD971F; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 2 • Clean</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Uro Normalization</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Pipe raw URL lists directly into <b>Uro</b> to strip static noise, tracking parameters, and duplicate endpoints.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #E6DB74; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #E6DB74; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 3 • Select</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Tool Playbooks & Tags</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Search 190+ tool YAML cheats with side-by-side tags (Nmap, Impacket, FFUF) and automatic variable injection.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #F92672; border-radius: 6px; padding: 12px 14px;">
                <div style="color: #F92672; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 4 • Execute</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Safe PTY Dispatch</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Verify <b>Tailscale</b> authorized lab status and dispatch commands directly to the live, persistent <b>PTY Terminal</b>.</div>
            </div>
        </div>
    </div>
    """
    st.markdown(steps_html, unsafe_allow_html=True)

    # Credits Section positioned under the Steps to Use section
    credits_html = """
    <div style="
        background: #1E1E1E;
        border: 1px solid #3E3D32;
        border-left: 4px solid #A6E22E;
        border-radius: 8px;
        padding: 14px 22px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    ">
        <div style="
            color: #A6E22E;
            font-weight: 700;
            font-size: 0.95rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.2px;
        ">
            Credits - Created by Aarush Rahul Patel
        </div>
        <div style="
            color: #FD971F;
            font-weight: 600;
            font-size: 0.92rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.2px;
        ">
            Research Partner  - Shreya Singh
        </div>
    </div>
    """
    st.markdown(credits_html, unsafe_allow_html=True)

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
        accent = tool_meta.get("accent", "#A6E22E")
        cats = tool_meta.get("categories", [])
        col = grid_cols[i % 3]

        with col:
            badges_html = render_category_chips_html(cats[:3])
            card_html = f"""
            <div style="
                background: #181818;
                border: 1px solid #3E3D32;
                border-top: 3px solid {accent};
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                min-height: 145px;
            ">
                <div style="font-weight: 700; color: #F8F8F2; font-size: 0.98rem; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace;">
                    {display_title}
                </div>
                <div style="color: #75715E; font-size: 0.84rem; line-height: 1.4; margin-bottom: 10px;">
                    {short_desc}
                </div>
                {badges_html}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    # Minimal clean bottom footer
    clean_footer_html = """
    <div style="
        border-top: 1px solid #3E3D32;
        margin-top: 32px;
        padding-top: 16px;
        padding-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    ">
        <div style="color: #75715E; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
            Web Crawler • Monokai Security Reconnaissance Workspace
        </div>
        <div style="color: #75715E; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
            v1.0.0
        </div>
    </div>
    """
    st.markdown(clean_footer_html, unsafe_allow_html=True)

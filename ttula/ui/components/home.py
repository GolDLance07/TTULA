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
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 22px;
        position: relative;
    ">
        <div style="
            font-size: 2.15rem;
            font-weight: 800;
            color: #A6E22E;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            font-family: 'JetBrains Mono', monospace;
        ">
            🕸️ WEB CRAWLER
        </div>
        <div style="
            color: #FD971F;
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 12px;
            font-family: 'Inter', sans-serif;
        ">
            Unified Security Reconnaissance & Automated Toolchain Workspace
        </div>
        <div style="
            color: #F8F8F2;
            font-size: 0.96rem;
            margin-bottom: 18px;
            font-family: 'JetBrains Mono', monospace;
        ">
            <span style="color: #A6E22E; font-weight: 700;">Credits:</span>
            <span style="color: #F8F8F2; font-weight: 600;">Developed by - Aarush Rahul Patel</span>
            <span style="color: #75715E; margin: 0 8px;">•</span>
            <span style="color: #FD971F; font-weight: 600;">Research and Development Partner - Shreya Singh</span>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span style="background: #272822; border: 1px solid #3E3D32; color: #A6E22E; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">RECONNAISSANCE</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #FD971F; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">IDENTITY OSINT</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #E6DB74; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">URL DE-NOISING</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #AE81FF; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">247+ PLAYBOOKS</span>
            <span style="background: #272822; border: 1px solid #3E3D32; color: #F92672; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">ZERO-TRUST GATED</span>
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
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 24px;
    ">
        <div style="font-size: 1.15rem; font-weight: 700; color: #A6E22E; margin-bottom: 14px; font-family: 'JetBrains Mono', monospace;">
            📋 Operational Workflow & Steps to Use
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #A6E22E; border-radius: 10px; padding: 14px 16px;">
                <div style="color: #A6E22E; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 1 • Discover</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Endpoint & Persona Recon</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Crawl target web ports with <b>Web Crawler</b> or discover user accounts across 60+ platforms with <b>Tookie</b>.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #FD971F; border-radius: 10px; padding: 14px 16px;">
                <div style="color: #FD971F; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 2 • Clean</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Uro Normalization</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Pipe raw URL lists directly into <b>Uro</b> to strip static noise, tracking parameters, and duplicate endpoints.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #E6DB74; border-radius: 10px; padding: 14px 16px;">
                <div style="color: #E6DB74; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 3 • Select</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Tool Playbooks & Tags</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Search 190+ tool YAML cheats with side-by-side tags (Nmap, Impacket, FFUF) and automatic variable injection.</div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-left: 3px solid #F92672; border-radius: 10px; padding: 14px 16px;">
                <div style="color: #F92672; font-weight: 700; font-size: 0.82rem; text-transform: uppercase; margin-bottom: 4px;">Step 4 • Execute</div>
                <div style="color: #F8F8F2; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">Safe PTY Dispatch</div>
                <div style="color: #75715E; font-size: 0.82rem; line-height: 1.45;">Verify <b>Tailscale</b> authorized lab status and dispatch commands directly to the live, persistent <b>PTY Terminal</b>.</div>
            </div>
        </div>
    </div>
    """
    st.markdown(steps_html, unsafe_allow_html=True)

    # Core Capabilities Matrix & Architectural Breakdown
    capabilities_html = """
    <div style="
        background: #181818;
        border: 1px solid #3E3D32;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 24px;
    ">
        <div style="font-size: 1.15rem; font-weight: 700; color: #FD971F; margin-bottom: 14px; font-family: 'JetBrains Mono', monospace;">
            🛡️ Core Architecture & Reconnaissance Subsystems
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #A6E22E; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">🕸️ Recursive Web Spidering</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    High-throughput crawler extracts endpoints, sub-paths, form targets, and script assets. Automated fallback ensures zero crash loops.
                </div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #FD971F; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">🔍 Tookie Identity Footprinting</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    OSINT engine querying 60+ social platforms, code hosting sites, and hacker forums for digital username footprints with configurable depth.
                </div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #E6DB74; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">🧹 Uro Normalization Pipeline</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    Removes duplicate query structures, tracking parameters (utm, fbclid), and static noise (png, css, js) to streamline tool inputs.
                </div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #AE81FF; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">📚 Arsenal-NG Knowledge Base</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    190+ tool YAML cheatsheets with side-by-side tags, live session variable substitution, and instant PTY command dispatch.
                </div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #F92672; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">🔒 Zero-Trust Mesh Coordinator</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    Tailscale WireGuard mesh node safety gate verifies node authorizations before high-impact credential audits can execute.
                </div>
            </div>
            <div style="background: #272822; border: 1px solid #3E3D32; border-radius: 10px; padding: 14px;">
                <div style="color: #66D9EF; font-weight: 700; font-size: 0.92rem; margin-bottom: 6px;">💻 Interactive Persistent PTY</div>
                <div style="color: #F8F8F2; font-size: 0.84rem; opacity: 0.85; line-height: 1.45;">
                    Direct zero-injection shell session running persistently in background, streaming output seamlessly across tab and UI interactions.
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(capabilities_html, unsafe_allow_html=True)

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
                border-radius: 10px;
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

    # Bottom Footer with Credits positioned in the bottom of the home page on the side
    footer_html = """
    <div style="
        border-top: 1px solid #3E3D32;
        margin-top: 36px;
        padding-top: 20px;
        padding-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    ">
        <div style="color: #75715E; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;">
            <div style="color: #A6E22E; font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">Web Crawler Workspace</div>
            <div>Automated Security Reconnaissance • Monokai v1.0.0</div>
            <div>🔒 Zero-Trust Boundary Enforced | WireGuard Mesh</div>
        </div>
        <div style="color: #75715E; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
            v1.0.0 • Active
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

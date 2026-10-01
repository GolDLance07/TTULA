"""Home Page Component for Web Crawler UI."""

import streamlit as st
from ttula.config.tools import TOOLS
from ttula.ui.components.badges import render_category_chips_html


def render_home_page(on_navigate=None) -> None:
    """Renders the clean, concise Home page for Web Crawler."""
    meta = TOOLS.get("home", {})

    home_hero_html = """
    <div style="
        background: #111820;
        border: 1px solid #27323D;
        border-radius: 12px;
        padding: 32px 36px;
        margin-bottom: 24px;
        position: relative;
    ">
        <div style="
            font-size: 2.2rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        ">
            WEB CRAWLER
        </div>
        <div style="
            color: #94A3B8;
            font-size: 1.05rem;
            line-height: 1.6;
            max-width: 780px;
            margin-bottom: 20px;
        ">
            A unified security reconnaissance workspace for web crawling,
            identity discovery, URL processing, OSINT workflows, and security command knowledge.
        </div>
        
        <div style="
            display: inline-block;
            background: #17212B;
            border: 1px solid #27323D;
            border-left: 3px solid #00F0FF;
            border-radius: 6px;
            padding: 8px 16px;
            margin-bottom: 8px;
        ">
            <span style="color: #64748B; font-size: 0.78rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Created by</span><br/>
            <span style="color: #F1F5F9; font-size: 0.95rem; font-weight: 600;">Aarush Rahul Patel &nbsp;·&nbsp; Shreya Singh</span>
        </div>
    </div>
    """
    st.markdown(home_hero_html, unsafe_allow_html=True)

    # Primary Action Buttons
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("🕸️ Start Crawling", use_container_width=True):
            st.session_state["nav_selection"] = "🕸️ Web Crawler"
            st.rerun()
    with col_b:
        if st.button("🔍 Identity OSINT", use_container_width=True):
            st.session_state["nav_selection"] = "🔍 Tookie (OSINT)"
            st.rerun()
    with col_c:
        if st.button("📚 Explore Cheats", use_container_width=True):
            st.session_state["nav_selection"] = "📚 Arsenal-NG"
            st.rerun()
    with col_d:
        if st.button("🌐 Lab Mesh Status", use_container_width=True):
            st.session_state["nav_selection"] = "🌐 Tailscale Mesh"
            st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Integrated Tools Grid
    st.markdown("### Integrated Security Toolchain")
    grid_cols = st.columns(3)

    tool_items = [
        ("web_crawler", "🕸️ Web Crawler", "Deep endpoint discovery & link extraction for target web hosts."),
        ("tookie", "🔍 Tookie", "Multi-platform OSINT account profiling across 500+ domains."),
        ("uro", "🧹 Uro", "High-efficiency URL normalization, parameter cleanup & noise removal."),
        ("arsenal", "📚 Arsenal-NG", "247+ tools & 2,900+ security command playbooks with variable injection."),
        ("legba", "🔐 Legba", "Fast multi-protocol authentication auditing for SSH, SMB, HTTP, and FTP."),
        ("tailscale", "🌐 Tailscale", "Zero-trust mesh network layer connecting authorized lab environments."),
    ]

    for i, (tool_id, display_title, short_desc) in enumerate(tool_items):
        tool_meta = TOOLS.get(tool_id, {})
        accent = tool_meta.get("accent", "#14B8A6")
        cats = tool_meta.get("categories", [])
        col = grid_cols[i % 3]

        with col:
            badges_html = render_category_chips_html(cats[:3])
            card_html = f"""
            <div style="
                background: #111820;
                border: 1px solid #27323D;
                border-top: 3px solid {accent};
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                min-height: 155px;
            ">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 1.0rem; margin-bottom: 4px;">
                    {display_title}
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem; line-height: 1.4; margin-bottom: 8px;">
                    {short_desc}
                </div>
                {badges_html}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

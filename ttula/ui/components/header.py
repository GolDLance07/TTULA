"""Reusable Arsenal-Style Tool Header Component for Web Crawler UI."""

from typing import Optional
import streamlit as st

from ttula.config.tools import get_tool_metadata
from ttula.ui.components.badges import render_category_chips_html


def render_tool_header(tool_key: str, custom_description: Optional[str] = None) -> None:
    """Renders a standardized Arsenal-style tool header:
    
    TOOL NAME
    Short description
    [Category] [Category] [Category]
    """
    meta = get_tool_metadata(tool_key)
    title = meta.get("title", tool_key.upper())
    desc = custom_description or meta.get("description", "")
    tagline = meta.get("tagline", "")
    accent = meta.get("accent", "#14B8A6")
    categories = meta.get("categories", [])
    icon = meta.get("icon", "")

    badges_html = render_category_chips_html(categories)

    header_html = f"""
    <div style="
        background: #111820;
        border: 1px solid #27323D;
        border-left: 4px solid {accent};
        border-radius: 8px;
        padding: 16px 20px 12px 20px;
        margin-bottom: 20px;
    ">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <span style="font-size: 1.3rem;">{icon}</span>
            <span style="
                font-size: 1.25rem;
                font-weight: 800;
                letter-spacing: 0.5px;
                color: #FFFFFF;
                font-family: inherit;
            ">{title}</span>
            <span style="
                color: #64748B;
                font-size: 0.85rem;
                margin-left: 6px;
            ">• {tagline}</span>
        </div>
        <div style="
            color: #94A3B8;
            font-size: 0.90rem;
            line-height: 1.45;
            margin-top: 4px;
        ">{desc}</div>
        {badges_html}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

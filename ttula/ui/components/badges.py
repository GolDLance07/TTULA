"""Reusable Category Badge / Chip Component for Web Crawler UI."""

from typing import List
from ttula.config.tools import CATEGORY_COLORS


def render_category_badge_html(category: str, custom_color: str = None) -> str:
    """Generates an HTML snippet for a single category badge."""
    color = custom_color or CATEGORY_COLORS.get(category, "#14B8A6")
    # Clean, compact chip with strong contrast on dark surface
    return (
        f'<span style="'
        f'display: inline-block; '
        f'background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.12); '
        f'color: {color}; '
        f'border: 1px solid rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.35); '
        f'border-radius: 6px; '
        f'padding: 3px 9px; '
        f'font-size: 0.70rem; '
        f'font-weight: 600; '
        f'text-transform: uppercase; '
        f'letter-spacing: 0.6px; '
        f'margin-right: 6px; '
        f'margin-bottom: 6px; '
        f'font-family: inherit;'
        f'">{category}</span>'
    )


def render_category_chips_html(categories: List[str]) -> str:
    """Generates a row of category badges."""
    badges_html = "".join(render_category_badge_html(cat) for cat in categories)
    return f'<div style="margin-top: 8px; margin-bottom: 12px; display: flex; flex-wrap: wrap;">{badges_html}</div>'

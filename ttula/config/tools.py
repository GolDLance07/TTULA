"""Centralized Tool Metadata and Category Vocabulary for Web Crawler.

Follows Arsenal-NG inspired information architecture:
Tool -> What does it do? -> What security domains does it belong to?
"""

from typing import Any, Dict, List

# Standardized Security Domain Category Vocabulary (Section 4)
CATEGORIES: List[str] = [
    "Recon",
    "OSINT",
    "Web Recon",
    "Network Recon",
    "Enumeration",
    "Identity Discovery",
    "URL Processing",
    "Service Enumeration",
    "Vulnerability Assessment",
    "Exploitation",
    "Post-Exploitation",
    "Wireless Security",
    "Authentication",
    "Credential Testing",
    "Digital Forensics",
    "Incident Response",
    "Information Gathering",
    "Command Reference",
    "Security Automation",
]

# Semantic Category Accents for High-Contrast Badges
CATEGORY_COLORS: Dict[str, str] = {
    "Recon": "#14B8A6",               # Teal
    "OSINT": "#8B5CF6",               # Violet
    "Web Recon": "#06B6D4",           # Cyan
    "Network Recon": "#38BDF8",       # Sky
    "Enumeration": "#10B981",         # Emerald
    "Identity Discovery": "#A78BFA",  # Light Violet
    "URL Processing": "#F59E0B",      # Amber
    "Service Enumeration": "#34D399", # Mint
    "Vulnerability Assessment": "#F97316", # Orange
    "Exploitation": "#EF4444",        # Red
    "Post-Exploitation": "#DC2626",   # Deep Red
    "Wireless Security": "#EC4899",   # Pink
    "Authentication": "#F43F5E",      # Rose
    "Credential Testing": "#E11D48",  # Crimson
    "Digital Forensics": "#6366F1",   # Indigo
    "Incident Response": "#84CC16",   # Lime
    "Information Gathering": "#0EA5E9", # Sky Blue
    "Command Reference": "#10B981",   # Emerald
    "Security Automation": "#64748B", # Slate
}

# Centralized Tool Registry (Section 5)
TOOLS: Dict[str, Dict[str, Any]] = {
    "home": {
        "id": "home",
        "name": "Home",
        "title": "WEB CRAWLER",
        "tagline": "Unified Security Reconnaissance Workspace",
        "description": "A unified security reconnaissance workspace for web crawling, identity discovery, URL processing, OSINT workflows, and security command knowledge.",
        "categories": ["Recon", "OSINT", "Web Recon", "Security Automation"],
        "accent": "#00F0FF",
        "icon": "⌂",
    },
    "web_crawler": {
        "id": "web_crawler",
        "name": "Web Crawler",
        "title": "WEB CRAWLER",
        "tagline": "Web crawling and endpoint discovery",
        "description": "High-throughput endpoint crawler and link extractor for target web services and mapped application ports.",
        "categories": ["Web Recon", "Information Gathering", "Recon"],
        "accent": "#00F0FF",
        "icon": "🕸️",
    },
    "tookie": {
        "id": "tookie",
        "name": "Tookie",
        "title": "TOOKIE",
        "tagline": "Username and identity OSINT tool",
        "description": "High-performance digital identity and username reconnaissance engine querying 500+ web platforms.",
        "categories": ["OSINT", "Identity Discovery", "Recon"],
        "accent": "#8B5CF6",
        "icon": "🔍",
    },
    "uro": {
        "id": "uro",
        "name": "Uro",
        "title": "URO",
        "tagline": "URL normalization and deduplication utility",
        "description": "Specialized URL filtering engine that eliminates duplicate endpoints, cleans tracking parameters, and filters static file noise.",
        "categories": ["Web Recon", "URL Processing", "Recon"],
        "accent": "#F59E0B",
        "icon": "🧹",
    },
    "arsenal": {
        "id": "arsenal",
        "name": "Arsenal-NG",
        "title": "ARSENAL-NG",
        "tagline": "Security command knowledge and operation reference",
        "description": "Curated security command repository with 247+ tools, 2,900+ actions, and live session variable substitution.",
        "categories": ["Recon", "Enumeration", "Exploitation", "Wireless Security", "Command Reference"],
        "accent": "#10B981",
        "icon": "📚",
    },
    "legba": {
        "id": "legba",
        "name": "Legba",
        "title": "LEGBA",
        "tagline": "Multi-protocol authentication testing utility",
        "description": "High-speed network authenticator auditing credentials across SSH, SMB, HTTP, and FTP in authorized lab environments.",
        "categories": ["Authentication", "Credential Testing"],
        "accent": "#EF4444",
        "icon": "🔐",
    },
    "tailscale": {
        "id": "tailscale",
        "name": "Tailscale Mesh",
        "title": "TAILSCALE",
        "tagline": "Secure peer-to-peer lab network boundary",
        "description": "Zero-trust WireGuard mesh coordinator providing authorized lab target discovery, health checks, and secure connectivity.",
        "categories": ["Network Recon", "Security Automation"],
        "accent": "#14B8A6",
        "icon": "🌐",
    },
    "terminal": {
        "id": "terminal",
        "name": "Live Terminal",
        "title": "TERMINAL PTY",
        "tagline": "Persistent interactive pseudoterminal session",
        "description": "Zero-injection argv executor running interactive shell sessions that persist across dashboard interactions.",
        "categories": ["Security Automation", "Command Reference"],
        "accent": "#38BDF8",
        "icon": "💻",
    },
}


def get_tool_metadata(tool_key: str) -> Dict[str, Any]:
    """Retrieve metadata for a tool by identifier with safe fallbacks."""
    key = tool_key.lower().replace("-", "_")
    if key in TOOLS:
        return TOOLS[key]
    for k, v in TOOLS.items():
        if k in key or key in k:
            return v
    return {
        "id": tool_key,
        "name": tool_key.capitalize(),
        "title": tool_key.upper(),
        "tagline": "Security operations tool",
        "description": "Integrated security utility.",
        "categories": ["Recon"],
        "accent": "#14B8A6",
        "icon": "⚙️",
    }

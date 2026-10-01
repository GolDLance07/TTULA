# TTULA — Web Crawler

**A Kali-native, terminal-first security reconnaissance workspace.**

TTULA ties together **Arsenal-NG** (command knowledge), **Tookie** (OSINT/URL discovery), **Uro** (URL deduplication), **Legba** (credential testing), and a custom **Web Crawler** into a single cohesive tool. All components communicate through a shared Python core — no shell piping, no manual file transfer.

> **Developed by** — Aarush Rahul Patel  
> **Research and Development Partner** — Shreya Singh

---

## ✨ Features

| Capability | Details |
|---|---|
| **Web Crawler** | Python-native `urllib` crawler with regex-based endpoint extraction — no external binary required |
| **Tookie OSINT** | Username-based identity and social footprint discovery with configurable URL limit |
| **Uro URL Filtering** | Deduplicates and normalizes raw URL collections to remove junk endpoints |
| **Arsenal-NG Cheats** | Tag-searched YAML command knowledge base with `{{variable}}` placeholder substitution |
| **Legba Auth Testing** | Strict lab-gated authentication command builder (requires `is_authorized_lab = True`) |
| **Tailscale Mesh** | Live mesh monitoring and 1-key lab authorization toggle in the TUI |
| **Persistent PTY** | Long-lived interactive shell session that survives UI reruns (tested: 50+ sequential commands) |
| **Visual TUI** | Monokai-themed Textual dashboard with tabbed navigation and a live terminal pane |
| **Streamlit UI** | Optional browser console for operators who prefer a web interface |

---

## 🏗️ Architecture & Data Flow

```
ttula (CLI)
     │
     ├── tui          ─► Textual TUI (default)
     └── ui           ─► Streamlit browser console
            │
            ▼
     TTULAEngine (core/engine.py)  ── no Streamlit dependency ──► headless / CLI / tests
            │
            ├── tailscale adapter   (integrations/tailscale/)
            ├── arsenal adapter     (integrations/arsenal/)
            ├── tookie adapter      (integrations/tookie/)
            ├── uro adapter         (integrations/uro/)
            ├── legba adapter       (integrations/legba/)
            └── web crawler adapter (integrations/crawler/)
                        │
                        ▼
               Execution Manager (execution/manager.py)   ← process-level singleton
                        │
               ┌────────┴────────┐
               ▼                 ▼
          PTY shell         Subprocess
      (pty.openpty)      (shell=False, argv)
```

### Security Guarantees
1. **Zero shell interpolation** — all commands are built as `argv: list[str]`. `shell=True` with string interpolation is never used.
2. **Explicit target gating** — Legba and active scans require a target explicitly marked `is_authorized_lab = True` in `~/.config/ttula/authorized_targets.json`.
3. **Command preview** — every command is shown to the operator before execution.
4. **Session persistence** — the PTY execution manager is a process-level singleton that survives Streamlit UI reruns.
5. **Localhost bound** — the Streamlit interface binds to `127.0.0.1` by default.

---

## 📂 Project Structure

```
TTULA/
├── ttula/
│   ├── cli/
│   │   └── main.py                 # CLI launcher — subcommands: tui, ui, crawl, recon, pipeline, cheats, doctor, setup-deps
│   ├── core/
│   │   ├── models.py               # Shared data models: Target, Command, URLCollection, ToolResult, TerminalSession
│   │   ├── operations.py           # Category/tag → command mapping and safe placeholder filling
│   │   └── engine.py               # Headless orchestration engine (no Streamlit dependency)
│   ├── execution/
│   │   ├── pty.py                  # POSIX PTY (openpty) + Windows subprocess fallback
│   │   ├── process.py              # Subprocess execution with strict argv lists
│   │   └── manager.py              # Process-level singleton session registry
│   ├── integrations/
│   │   ├── arsenal/
│   │   │   ├── adapter.py          # YAML cheat loader, tag search, {{variable}} substitution
│   │   │   └── cheats/             # Bundled curated cheats (auth.yaml, network.yaml, web.yaml)
│   │   ├── crawler/
│   │   │   └── adapter.py          # urllib-based web crawler + regex endpoint extractor
│   │   ├── tookie/
│   │   │   └── adapter.py          # Tookie OSINT username discovery with configurable result limit
│   │   ├── uro/
│   │   │   └── adapter.py          # Uro URL deduplication (binary + Python native fallback)
│   │   ├── legba/
│   │   │   └── adapter.py          # Lab-gated authentication command builder
│   │   └── tailscale/
│   │       └── adapter.py          # Tailscale status, IP, netcheck, authorization caching
│   ├── config/
│   │   └── tools.py                # Central tool metadata: names, descriptions, categories, Monokai accent colors
│   ├── ui/
│   │   ├── tui/
│   │   │   └── app.py              # Textual TUI — Monokai theme, tabbed navigation, live PTY pane
│   │   ├── streamlit/
│   │   │   └── app.py              # Streamlit browser console
│   │   └── components/
│   │       ├── home.py             # Home tab: capabilities matrix, workflow steps, credits
│   │       ├── header.py           # Reusable tool header with Arsenal-style category badges
│   │       └── badges.py           # Category badge rendering
│   └── utils/
│       └── config.py               # Config directory and temp path resolution
├── cheat-files/                     # Full Arsenal-NG community YAML knowledge base (190+ tools)
├── tests/                           # pytest suite (28 tests, all passing)
├── scripts/
│   └── build_deb.sh                # Debian .deb packaging script
├── debian/                          # Debian package metadata (control, rules, changelog)
├── pyproject.toml                   # Python package config and entry point
└── Dockerfile                       # Container image definition
```

---

## 🚀 Quick Start

### Installation
```bash
# Clone and install in development mode
git clone <repo-url> && cd TTULA
pip install -e .
```

### Launch the TUI (default)
```bash
ttula
# Or explicitly:
ttula tui
```

Navigate with hotkeys: `1–5` to switch tabs, `Space` to toggle lab authorization, `Enter` to execute.

### Launch the Streamlit Browser Console (optional)
```bash
ttula ui --host 127.0.0.1 --port 8501
# Open: http://127.0.0.1:8501
```

---

## 🖥️ CLI Reference

```bash
# Launch native Textual TUI (default)
ttula tui

# Launch Streamlit web console
ttula ui [--host HOST] [--port PORT]

# Crawl a web service and extract endpoints
ttula crawl <url> [--max-pages N]

# Tailscale mesh status
ttula tailscale

# Run Tookie OSINT discovery
ttula recon <username> [--limit N] [--timeout SECONDS]

# Tookie → Uro end-to-end pipeline (no manual file transfer)
ttula pipeline <username> [--limit N] [--timeout SECONDS]

# Search Arsenal-NG cheat corpus
ttula cheats [query]
ttula cheats nmap
ttula cheats "web fuzzing"

# System health check
ttula doctor

# Install missing toolchain dependencies
ttula setup-deps
```

---

## 📖 Cheat Knowledge Base

The `cheat-files/` directory contains the full **Arsenal-NG community YAML knowledge base** (190+ security tools including nmap, sqlmap, metasploit, ffuf, nuclei, etc.). Each YAML file holds curated commands, tags, and `{{variable}}` placeholders for the respective tool.

The Arsenal adapter loads and searches these files at runtime. Use `ttula cheats <query>` or the Arsenal tab in the TUI to search by tool name, category tag, or keyword.

---

## 🧪 Testing

```bash
# Run the full test suite
python -m pytest tests/ -v
```

| Test File | Coverage |
|---|---|
| `test_core_and_execution.py` | Data models, argv safety, placeholder gating, session continuity |
| `test_endurance.py` | PTY survives 50+ sequential commands without respawn |
| `test_tailscale.py` | Status parsing, authorization caching, offline fallback |
| `test_arsenal.py` | YAML loading, tag/category search, placeholder detection |
| `test_crawler_and_tools.py` | Web crawler endpoint discovery and regex extraction |
| `test_tookie_uro_pipeline.py` | OSINT discovery, URL dedup, end-to-end pipeline |
| `test_legba.py` | Lab safety refusal, SSH/HTTP command building |
| `test_engine.py` | Core engine wiring and adapter dispatch |
| `test_full_workflow.py` | Phase 1–6 orchestration end-to-end |
| `test_ui_persistence.py` | PTY session persists across UI reruns |
| `test_tui.py` | Textual TUI composability and tab navigation |

---

## 📦 Packaging (Debian / Kali)

```bash
# Build a .deb for native Kali installation
chmod +x scripts/build_deb.sh
./scripts/build_deb.sh

# Install on Kali
sudo apt install ./ttula_0.1.0-1_all.deb
ttula
```

---

## 🐳 Docker

```bash
docker build -t ttula .
docker run --rm -it ttula tui
```

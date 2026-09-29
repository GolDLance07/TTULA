# TTULA (Security Operations Orchestration Tool)

**Personal, Kali-native orchestration layer for controlled security lab workflows.**

TTULA connects **Arsenal-NG** (command knowledge), **Tookie** (OSINT/URL discovery), **Uro** (URL processing), and **Legba** (auth testing capability), connected via **Tailscale** to an authorized vulnerable lab server, executed through a **persistent PTY session**, and controlled from a sleek dark-mode **Streamlit browser UI** or headless CLI.

---

## 🛡️ Architecture & Data Flow

```
Browser UI (Streamlit)  ──►  Core Engine (TTULAEngine)  ──►  Adapters (Tailscale / Arsenal / Tookie / Uro / Legba)
                                     │
                                     ▼
                            Execution Manager (Singleton)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       Interactive PTY Shell                 Subprocess (Non-interactive)
   (POSIX pty.openpty / bash)                  (Strict argv lists, shell=False)
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                      Tailscale Private Lab Mesh
                                     ▼
                       Authorized Lab Target Only
```

### Core Security Guarantees
1. **Zero Shell Interpolation**: All tool commands are built strictly as `argv: list[str]`. No `shell=True` with string concatenation.
2. **Explicit Target Gating**: Lab targets must be explicitly authorized (`is_authorized_lab = True`) via local configuration (`~/.config/ttula/authorized_targets.json`) before any active scan or Legba test can run.
3. **Command Preview**: Every command is presented to the operator in the UI with shell escaping before execution.
4. **Session Persistence**: The PTY execution manager is a process-level singleton that survives Streamlit UI reruns (tested for ≥50 sequential interactions).
5. **Localhost Bound**: The Streamlit control interface binds only to `127.0.0.1` by default.

---

## 📂 Project Structure

```
c:/TTULA/
├── ttula/
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py                 # Multi-command CLI launcher
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py               # Target, Command, URLCollection, ToolResult, etc.
│   │   ├── operations.py           # Category mapping & safe placeholder filling
│   │   └── engine.py               # Headless orchestration engine
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── pty.py                  # POSIX PTY (openpty) + cross-platform shell
│   │   ├── process.py              # Subprocess execution with strict argv lists
│   │   └── manager.py              # Process-level singleton session registry
│   ├── integrations/
│   │   ├── tailscale/adapter.py    # `tailscale status --json`, netcheck, lab authorization
│   │   ├── arsenal/
│   │   │   ├── adapter.py          # Cheatsheet loader & tag-based relevance search
│   │   │   └── cheats/             # Bundled YAML cheats (network, web, auth, etc.)
│   │   ├── tookie/adapter.py       # Tookie OSINT username discovery
│   │   ├── uro/adapter.py          # Managed temp file Uro URL cleaner & native engine
│   │   └── legba/adapter.py        # Strict lab-gated authentication command builder
│   ├── ui/streamlit/app.py         # Cyber dark glassmorphism Streamlit control surface
│   └── utils/config.py             # Config & temp paths
├── scripts/
│   ├── pty_prototype.py            # Standalone PTY verification prototype (Step 1)
│   └── build_deb.sh                # Debian .deb build script
├── tests/                          # Full pytest test suite (20 tests)
├── debian/                         # Debian packaging (control, rules, changelog)
└── pyproject.toml                  # Python package configuration
```

---

## 🚀 Quick Start

### 1. Requirements & Installation
Install TTULA in development mode:
```bash
pip install -e .
```

### 2. Launch the Native Visual Terminal Dashboard (Default)
```bash
ttula
# Or explicitly:
ttula tui
```
Runs directly in your terminal with hotkey navigation (`1-5` for tabs, `Space` to toggle lab authorization, `Enter` to execute).

### 3. Launch the Optional Streamlit Web Console
```bash
ttula ui --host 127.0.0.1 --port 8501
```
Access the dark-mode cyber console at `http://127.0.0.1:8501`.

### 3. Headless CLI Commands
```bash
# Check Tailscale status and discovered devices
ttula tailscale

# Search Arsenal command cheatsheets
ttula cheats nmap
ttula cheats "web fuzzing"

# Run Tookie OSINT discovery
ttula recon <username>

# Run end-to-end Tookie -> Uro pipeline without manual file transfer
ttula pipeline <username>
```

---

## 🧪 Testing & Verification

Run the entire automated test suite:
```bash
python -m pytest tests/ -v
```

### Test Coverage Highlights:
- `test_core_and_execution.py`: Data models, argv validation, placeholder safety gate, process runner, session continuity.
- `test_endurance.py`: Endurance testing running 50+ sequential commands in a single session without failure.
- `test_tailscale.py`: Status parsing, node discovery, explicit authorization caching, offline fallback.
- `test_arsenal.py`: YAML cheatsheet loading, category and tag-based relevance search, placeholder detection.
- `test_tookie_uro_pipeline.py`: OSINT discovery, Uro URL filtering and deduplication, end-to-end pipeline.
- `test_legba.py`: Lab safety refusal, SSH/HTTP command building with conservative concurrency defaults.
- `test_ui_persistence.py`: Verification that PTY session survives across multiple UI rerun cycles.
- `test_full_workflow.py`: Complete Phase 1–6 end-to-end orchestration workflow.

---

## 📦 Debian (.deb) Packaging

To package TTULA for native installation on Kali Linux (`sudo apt install ./ttula_0.1.0-1_all.deb`):

```bash
chmod +x scripts/build_deb.sh
./scripts/build_deb.sh
```

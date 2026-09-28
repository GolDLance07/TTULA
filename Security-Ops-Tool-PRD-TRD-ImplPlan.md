# Security Operations Orchestration Tool
## PRD · TRD · Implementation & Testing Plan (v1.0)

Personal, Kali-native orchestration layer for a controlled security lab. Combines Arsenal-NG (command knowledge), Tookie (OSINT/URL discovery), Uro (URL processing), and Legba (auth testing capability), connected via Tailscale to an authorized vulnerable lab server, executed through a persistent PTY, controlled from a Streamlit browser UI, and eventually distributed as a `.deb`.

---

# PART 1 — PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1.1 Problem Statement
Running a personal security-lab workflow today means manually: looking up commands, running OSINT tools, hand-copying URL lists between tools, remembering credential-testing syntax, and juggling terminal windows across a Tailscale-connected lab. This is slow and error-prone, and nothing captures the workflow as reusable, structured state.

## 1.2 Goal
Build a single Python-native application that lets one operator (the owner) run coherent, multi-stage workflows — recon → URL processing → command discovery → execution/auth-testing — against **their own authorized lab target**, from a browser control surface, on native Kali.

## 1.3 Non-Goals (v1)
- Not a multi-user platform, not a SaaS product, no public API.
- Not a replacement for Arsenal-NG/Tookie/Uro/Legba — it orchestrates them.
- No cloud infra, Docker/K8s, microservices, or distributed execution in v1.
- No RAG/semantic search in v1 (documented as a possible v2 enhancement).
- No support for targets outside the owner's authorized lab/tailnet.

## 1.4 Target User
Single operator (the project owner), using a Kali ThinkPad against a vulnerable server they own, both joined to a private tailnet.

## 1.5 User Stories
1. As the operator, I can see whether Tailscale is up and which devices (execution node, lab target) are online.
2. As the operator, I can run Tookie against a username/target and get a structured URL/data collection back in the UI, without copying text by hand.
3. As the operator, I can send that collection to Uro with one click and see the cleaned result.
4. As the operator, I can pick an operation category (e.g. "service enumeration") and see candidate commands from Arsenal-NG's corpus.
5. As the operator, I can review a generated command before it runs, then execute it against the explicit execution node, watching live output.
6. As the operator, I can launch a Legba authentication test against an explicitly selected target/service, with the command shown before execution.
7. As the operator, I can keep a running terminal session alive across UI interactions (no shell re-spawn per click).
8. As the operator, I can eventually install the whole thing with `sudo apt install our-tool` and just run `our-tool`.

## 1.6 Success Criteria
- End-to-end workflow (Tookie → Uro → Arsenal → execute) runs on native Kali without manual file-copying.
- PTY session survives across ≥50 sequential UI-triggered commands in one sitting.
- Every executed command is shown to the operator before/at execution (no silent execution from untrusted data).
- Legba/authentication commands only run against an explicitly configured lab target, never inferred from raw scan output.
- Packaged `.deb` installs cleanly on a fresh Kali VM and launches the control UI.

## 1.7 Key Risks
| Risk | Mitigation |
|---|---|
| Command injection via string concatenation | Core passes structured `Command` objects; adapters build argv lists, not shell strings |
| Streamlit rerun kills PTY session | Explicit session/process manager outside Streamlit's rerun lifecycle (module-level singleton or subprocess kept alive) |
| Scope creep onto real/unauthorized targets | `Target` object requires explicit tailnet-membership check before any execution or Legba run |
| Over-engineering before core is proven | Build order enforced (see Part 3): PTY prototype → core → adapters → UI → packaging |

---

# PART 2 — TECHNICAL REQUIREMENTS DOCUMENT (TRD)

## 2.1 Architecture Overview

```
Browser → Streamlit (control surface) → Core Engine → Adapters (Arsenal / Tookie / Uro / Legba / Tailscale)
                                              ↓
                                     Execution Manager → PTY → Kali shell → (Tailscale) → Lab Target
```

Principle: **the application is the Python core; Streamlit is a swappable UI.** The core must be usable headless (e.g. from a CLI or test script) with no Streamlit import.

## 2.2 Core Data Model

```python
Target(name, tailscale_ip, is_authorized_lab: bool)
ExecutionNode(name, local: bool, capabilities: list[str])
Operation(name, category, target: Target | None)
Command(source_tool, title, description, argv: list[str])   # argv, never a raw shell string
URLCollection(items: list[str], source_tool, created_at)
ToolResult(tool, stdout, stderr, exit_code, structured_data)
TerminalSession(id, node: ExecutionNode, pty_fd, alive: bool)
```

All inter-tool data flows through these objects — never raw shell pipes between adapters.

## 2.3 Module Layout

```
our_tool/
├── cli/main.py                # launcher: init core, start execution manager, launch Streamlit
├── core/
│   ├── engine.py               # orchestrates adapters + execution manager
│   ├── operations.py           # operation → command-candidate mapping (tags-based, v1)
│   └── models.py                # data classes above
├── execution/
│   ├── manager.py               # session registry, lifecycle, survives UI reruns
│   ├── pty.py                    # low-level PTY create/read/write
│   └── process.py               # subprocess fallback for non-interactive tools
├── integrations/
│   ├── arsenal/adapter.py       # loads/queries YAML cheat corpus → Command candidates
│   ├── tookie/adapter.py        # runs tookie, parses output → URLCollection / structured hits
│   ├── uro/adapter.py            # writes temp file, runs uro, reads output → URLCollection
│   ├── legba/adapter.py          # builds validated Command for auth testing, requires Target
│   └── tailscale/adapter.py      # `tailscale status --json`, ip, netcheck wrappers
├── ui/streamlit/app.py           # thin control surface calling core.engine
└── utils/
```

## 2.4 Component Specs

### 2.4.1 Execution Manager / PTY
- Owns one or more `TerminalSession`s keyed by session id, stored in a process-level singleton (not Streamlit session_state) so it survives reruns.
- API: `create_session(node) -> session_id`, `send(session_id, argv|str)`, `read(session_id) -> ToolResult stream`, `kill(session_id)`.
- v1 prototype target: spawn PTY + bash, send command, read output, keep alive, send second command, read output — proven standalone before any UI work.
- Long-running/streaming commands (e.g. Legba) must support incremental read, not just capture-on-exit.

### 2.4.2 Tailscale Adapter
- Wraps `tailscale status --json`, `tailscale ip`, `tailscale netcheck`.
- Produces `Target`/`ExecutionNode` objects; flags a device as `is_authorized_lab` only via explicit local config (never auto-inferred from the tailnet device list).

### 2.4.3 Arsenal-NG Adapter
- Reads the YAML cheat corpus (does not shell out to arsenal-ng's TUI; no TIOCSTI dependency).
- v1 retrieval: tag/operation string match → ranked candidate list of `Command` objects with placeholders unfilled.
- Placeholder filling happens in `core.operations`, using explicit `Target`/`ExecutionNode` values — never blind string substitution from untrusted data.
- v2 candidate (explicitly deferred): semantic/RAG retrieval over the same corpus.

### 2.4.4 Tookie Adapter
- Invokes `tookie-osint` via Execution Manager (subprocess, not necessarily PTY) with structured args (`-u`, `-U`, `-o json`).
- Parses JSON output into `URLCollection`/hit list; never trusts platform match as identity confirmation (surfaced as "possible match" in UI per Tookie's own guidance).

### 2.4.5 Uro Adapter
- Accepts a `URLCollection`, writes it to a managed temp file under `/tmp/our-tool/`, invokes `uro -i <file> -o <outfile>`, reads result back into a new `URLCollection`.
- Temp files cleaned up after read; adapter is the only place that knows a file was involved.

### 2.4.6 Legba Adapter
- Builds a `Command` (argv form) for a specific protocol subcommand, **only** when called with an explicit `Target` marked `is_authorized_lab = True`.
- Never accepts a target string sourced directly from Tookie/Uro output without operator confirmation in the UI.
- Concurrency (`-c`) defaults conservative; adapter surfaces Legba's own rate-limit/lockout warnings from the reference doc to the UI.

### 2.4.7 Streamlit UI
- Pure control surface: renders state from `core.engine`, sends operator actions to it, shows command-preview-before-execute for every executable action, streams `ToolResult` output.
- No tool-specific logic lives in `ui/`.

## 2.5 Security Requirements (binding)
- All commands built as argv lists; no shell string interpolation of untrusted data.
- Command shown to operator before execution for anything beyond passive recon.
- Legba/credential-testing gated on explicit, locally-configured lab target.
- Streamlit bound to localhost/tailnet only by default; never exposed publicly.
- No credential persistence beyond the current session unless explicitly exported by the operator.

## 2.6 Packaging
- Dev: `pyproject.toml` + venv.
- Distribution target: Debian package (`debian/control`, `rules`) → `sudo apt install our-tool` → `our-tool` launches CLI → initializes core → starts Streamlit bound to localhost.

---

# PART 3 — IMPLEMENTATION & TESTING PLAN

## 3.1 Build Order (enforced)
1. **PTY prototype** (standalone script, no core/UI): spawn PTY+bash, send/read two sequential commands reliably on native Kali.
2. **Core skeleton**: data models + `engine.py` with no adapters wired, unit-testable.
3. **Execution Manager**: wrap the proven PTY prototype behind the session API; add subprocess fallback for non-interactive tools.
4. **Tailscale adapter**: read-only status/ip/netcheck wrapping; manual test against real tailnet.
5. **Arsenal adapter**: load real YAML corpus, tag-search, return `Command` candidates; unit tests against sample cheat files.
6. **Tookie adapter**: run against a test username, verify JSON parse → `URLCollection`.
7. **Uro adapter**: feed a known `URLCollection`, verify dedup/filter behavior matches manual CLI run.
8. **Tookie→Uro pipeline test**: end-to-end without any manual file handling.
9. **Legba adapter**: build commands only, dry-run (print argv) against lab target config; only execute after PTY/session layer is trusted.
10. **Streamlit control layer**: wire engine calls, verify PTY session survives reruns (this is the single highest-risk integration point — test explicitly).
11. **Full workflow test** on native Kali ThinkPad against the vulnerable lab server over Tailscale.
12. **Packaging**: build `.deb`, install on a clean Kali VM, verify `our-tool` launches end-to-end.

## 3.2 Test Matrix

| Layer | Test type | Example cases |
|---|---|---|
| PTY/Execution Manager | Unit + manual | session survives 50+ sequential commands; kill/cleanup on crash; concurrent sessions don't cross-write |
| Tailscale adapter | Integration | correctly identifies execution node vs. configured lab target; handles Tailscale down/not installed |
| Arsenal adapter | Unit | tag search returns expected candidates for known corpus fixtures; placeholder detection |
| Tookie adapter | Integration | JSON output parses into correct `URLCollection`; handles zero-result case; handles malformed output gracefully |
| Uro adapter | Integration | dedup matches manual `uro -i` run on identical input; temp files cleaned up after run |
| Legba adapter | Unit + manual (lab only) | refuses to build command without `is_authorized_lab=True` target; concurrency defaults enforced; command preview matches what actually executes |
| Streamlit UI | Manual + smoke | PTY session state persists across button clicks/reruns; command-preview shown before every execute action |
| End-to-end | Manual, on lab | full Phase 1–6 workflow from the handoff doc runs against the real vulnerable server over Tailscale |
| Packaging | Manual | fresh Kali VM, `apt install` the local `.deb`, launch, confirm UI reachable on localhost only |

## 3.3 Acceptance Criteria for v1 "Done"
- All 12 build-order steps completed and individually tested.
- Full workflow (Phase 1–6 from the architecture doc) demonstrated end-to-end on native Kali against the owned lab target.
- No shell-string command construction anywhere in the codebase (grep-verified: no `shell=True` with interpolated strings).
- `.deb` install verified on a clean VM.

## 3.4 Explicitly Deferred (v2+)
- RAG/semantic retrieval for Arsenal.
- Multi-user/auth, public API, cloud/K8s deployment.
- Any target outside the operator's own tailnet.

"""CLI launcher for TTULA.

Initializes the core engine, manages terminal sessions, and launches
the Streamlit UI or headless CLI subcommands.
"""

from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path
from ttula.core.engine import create_default_engine
from ttula.execution.manager import get_execution_manager


def launch_ui(host: str = "127.0.0.1", port: int = 8501):
    """Launch Streamlit control surface bound strictly to localhost or specified host."""
    app_path = Path(__file__).parent.parent / "ui" / "streamlit" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--theme.base",
        "dark",
    ]
    print(f"[*] Launching TTULA Operator Console at http://{host}:{port}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Shutting down TTULA UI...")
        get_execution_manager().cleanup_all()


def cmd_tailscale():
    engine = create_default_engine()
    status = engine.get_tailscale_status()
    print("=== TTULA Tailscale Status ===")
    print(f"Online: {status.get('online')}")
    print(f"Self IP: {status.get('self_ip')}")
    print("\nDevices:")
    for d in status.get("devices", []):
        lab_tag = " [AUTHORIZED LAB]" if d.get("is_authorized_lab") else ""
        print(f" - {d['name']} ({d['ip']}) [{d.get('os', 'unknown')}]{lab_tag}")


def cmd_recon(username: str):
    engine = create_default_engine()
    print(f"[*] Running OSINT discovery for username: {username}")
    res = engine.run_tookie(username)
    print(f"[+] Found {res.count()} endpoints.")
    for item in res.items:
        print(f"  -> {item}")


def cmd_pipeline(username: str):
    engine = create_default_engine()
    print(f"[*] Executing Tookie -> Uro pipeline for username: {username}")
    res = engine.run_tookie_uro_pipeline(username)
    print(f"[+] Raw URLs: {res['raw_count']} -> Cleaned URLs: {res['cleaned_count']}")
    for item in res["cleaned_collection"].items:
        print(f"  -> {item}")


def cmd_cheats(query: str):
    engine = create_default_engine()
    cmds = engine.find_commands(query)
    print(f"=== Arsenal Cheats for '{query}' ({len(cmds)} matches) ===")
    for c in cmds:
        print(f"\n[+] {c.title}")
        print(f"    Description: {c.description}")
        print(f"    Command:     {c.display_string}")
        print(f"    Placeholders:{list(c.placeholders.keys())}")


def cmd_doctor():
    """Diagnostic system health check for Kali Linux environment and tools."""
    import shutil
    import platform
    from ttula.utils.config import get_config_dir

    print("\n" + "=" * 55)
    print("      TTULA Kali System & Toolchain Diagnostics")
    print("=" * 55)

    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    print(f"[*] Operating System:  {os_info}")
    print(f"[*] Python Version:    {platform.python_version()}")
    print(f"[*] Config Directory:  {get_config_dir()}")

    # Check PTY support
    pty_status = "Available (POSIX native)" if os.name != "nt" else "Emulated (Windows fallback)"
    print(f"[*] PTY Subsystem:     {pty_status}")

    tools = [
        ("Tailscale Mesh", "tailscale", "sudo apt install tailscale && sudo tailscale up"),
        ("Tookie OSINT", "tookie-osint", "pip install tookie-osint"),
        ("Uro URL Filter", "uro", "pip install uro"),
        ("Legba Auth Tester", "legba", "cargo install legba OR download binary to /usr/local/bin"),
        ("Nmap Port Scanner", "nmap", "sudo apt install nmap"),
    ]

    print("\n[+] Integrated Tools Status:")
    all_ok = True
    for label, bin_name, fix in tools:
        path = shutil.which(bin_name)
        if path:
            print(f"  [+] {label:<20} -> {path}")
        else:
            print(f"  [-] {label:<20} -> NOT FOUND")
            print(f"      Fix: {fix}")
            all_ok = False

    print("\n" + "-" * 55)
    if all_ok:
        print("[+] All toolchain dependencies are installed and ready!")
    else:
        print("[!] Some tools are missing. Run `ttula setup-deps` or use the fixes above.")
    print("=" * 55 + "\n")


def cmd_setup_deps():
    """Helps install missing Python and Kali dependencies."""
    import shutil
    print("[*] Installing Python dependencies (tookie-osint, uro)...")
    cmd = [sys.executable, "-m", "pip", "install", "tookie-osint", "uro"]
    try:
        subprocess.run(cmd, check=True)
        print("[✓] Python dependencies installed successfully.")
    except Exception as e:
        print(f"[!] Pip install failed: {e}")

    if not shutil.which("tailscale"):
        print("\n[!] Tailscale not detected. On Kali/Debian, install with:")
        print("    curl -fsSL https://tailscale.com/install.sh | sh")

    if not shutil.which("legba"):
        print("\n[!] Legba not detected. Install via precompiled binary or cargo:")
        print("    curl -sSfL https://raw.githubusercontent.com/evilsocket/legba/master/install.sh | sudo sh")


def main():
    parser = argparse.ArgumentParser(
        prog="ttula",
        description="TTULA - Security Operations Orchestration Tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # UI command
    ui_parser = subparsers.add_parser("ui", help="Launch Streamlit browser console")
    ui_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    ui_parser.add_argument("--port", type=int, default=8501, help="Bind port (default: 8501)")

    # Tailscale command
    subparsers.add_parser("tailscale", help="Check Tailscale status and targets")

    # Recon command
    recon_parser = subparsers.add_parser("recon", help="Run Tookie OSINT discovery")
    recon_parser.add_argument("username", help="Target username to investigate")

    # Pipeline command
    pipe_parser = subparsers.add_parser("pipeline", help="Run Tookie -> Uro pipeline")
    pipe_parser.add_argument("username", help="Target username for end-to-end pipeline")

    # Cheats command
    cheats_parser = subparsers.add_parser("cheats", help="Search Arsenal cheat corpus")
    cheats_parser.add_argument("query", nargs="?", default="", help="Search query or category")

    # Doctor command
    subparsers.add_parser("doctor", help="Check system prerequisites and toolchain health")

    # Setup-deps command
    subparsers.add_parser("setup-deps", help="Automate installation of toolchain dependencies")

    args = parser.parse_args()

    if args.command == "ui" or args.command is None:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8501)
        launch_ui(host=host, port=port)
    elif args.command == "tailscale":
        cmd_tailscale()
    elif args.command == "recon":
        cmd_recon(args.username)
    elif args.command == "pipeline":
        cmd_pipeline(args.username)
    elif args.command == "cheats":
        cmd_cheats(args.query)
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "setup-deps":
        cmd_setup_deps()


if __name__ == "__main__":
    main()


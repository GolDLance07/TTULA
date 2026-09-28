#!/usr/bin/env python3
"""Standalone PTY Prototype for TTULA.

Step 1 of Implementation Plan:
Proves spawning an interactive shell, sending two sequential commands,
and reading output reliably without respawning the shell.
Native on Kali/Linux using `pty`, with fallback emulation on Windows.
"""

import os
import sys
import time

def run_posix_pty():
    import pty
    import select
    import termios

    print("[+] Initializing POSIX Native PTY prototype...")
    master_fd, slave_fd = pty.openpty()

    pid = os.fork()
    if pid == 0:
        # Child process: spawn bash connected to slave PTY
        os.close(master_fd)
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        
        # Launch bash
        os.environ["PS1"] = "__TTULA_PROMPT__$ "
        os.environ["TERM"] = "dumb"
        os.execlp("bash", "bash", "--noprofile", "--norc")
        sys.exit(1)

    # Parent process
    os.close(slave_fd)

    def read_until(sentinel: str, timeout: float = 3.0) -> str:
        buffer = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if r:
                chunk = os.read(master_fd, 4096).decode("utf-8", errors="replace")
                if chunk:
                    buffer.append(chunk)
                    full_text = "".join(buffer)
                    if sentinel in full_text:
                        return full_text
        return "".join(buffer)

    def send_cmd(cmd_str: str):
        os.write(master_fd, (cmd_str + "\n").encode("utf-8"))

    try:
        # Wait for initial prompt
        initial = read_until("__TTULA_PROMPT__", timeout=2.0)
        print(f"[+] Shell spawned. Initial output captured ({len(initial)} bytes).")

        # Command 1
        cmd1 = "echo 'TEST_SEQ_1_SUCCESS'"
        print(f"[+] Sending command 1: {cmd1}")
        send_cmd(cmd1)
        out1 = read_until("TEST_SEQ_1_SUCCESS", timeout=2.0)
        assert "TEST_SEQ_1_SUCCESS" in out1, f"Command 1 failed. Output: {out1}"
        print("[OK] Command 1 output verified.")

        # Command 2 (proves session continuity in the same shell)
        cmd2 = "echo 'TEST_SEQ_2_SUCCESS'"
        print(f"[+] Sending command 2: {cmd2}")
        send_cmd(cmd2)
        out2 = read_until("TEST_SEQ_2_SUCCESS", timeout=2.0)
        assert "TEST_SEQ_2_SUCCESS" in out2, f"Command 2 failed. Output: {out2}"
        print("[OK] Command 2 output verified.")

        # Verify persistent variable across commands
        send_cmd("SESSION_VAR='ttula_active'")
        time.sleep(0.1)
        send_cmd("echo \"VAR=$SESSION_VAR\"")
        out3 = read_until("VAR=ttula_active", timeout=2.0)
        assert "VAR=ttula_active" in out3, f"Persistence failed. Output: {out3}"
        print("[OK] Shell environment continuity verified across commands.")

        print("\n[SUCCESS] Step 1 POSIX PTY Prototype PASSED successfully!")
        return 0

    finally:
        os.close(master_fd)
        try:
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except OSError:
            pass

def run_windows_fallback():
    import subprocess
    import threading
    import queue

    print("[*] Running on Windows: executing prototype using persistent Subprocess Shell...")
    proc = subprocess.Popen(
        ["cmd.exe", "/Q", "/K"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    q = queue.Queue()

    def reader():
        for line in iter(proc.stdout.readline, ""):
            q.put(line)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    def send_and_read(cmd: str, expected: str, timeout: float = 3.0) -> str:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
        accum = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                line = q.get(timeout=0.1)
                accum.append(line)
                if expected in "".join(accum):
                    return "".join(accum)
            except queue.Empty:
                pass
        return "".join(accum)

    # Command 1
    cmd1 = "echo TEST_SEQ_1_SUCCESS"
    print(f"[+] Sending command 1: {cmd1}")
    out1 = send_and_read(cmd1, "TEST_SEQ_1_SUCCESS")
    assert "TEST_SEQ_1_SUCCESS" in out1, f"Command 1 failed: {out1}"
    print("[OK] Command 1 output verified.")

    # Command 2
    cmd2 = "echo TEST_SEQ_2_SUCCESS"
    print(f"[+] Sending command 2: {cmd2}")
    out2 = send_and_read(cmd2, "TEST_SEQ_2_SUCCESS")
    assert "TEST_SEQ_2_SUCCESS" in out2, f"Command 2 failed: {out2}"
    print("[OK] Command 2 output verified.")

    # Variable persistence check
    send_and_read("set TEST_VAR=ttula_windows_active", "ttula_windows_active", timeout=1.0)
    out3 = send_and_read("echo VAR=%TEST_VAR%", "VAR=ttula_windows_active")
    assert "VAR=ttula_windows_active" in out3, f"Persistence failed: {out3}"
    print("[OK] Shell environment continuity verified across commands.")

    proc.terminate()
    print("\n[SUCCESS] Step 1 Windows Fallback Prototype PASSED successfully!")
    return 0

def main():
    if os.name != "nt":
        return run_posix_pty()
    else:
        return run_windows_fallback()

if __name__ == "__main__":
    sys.exit(main())

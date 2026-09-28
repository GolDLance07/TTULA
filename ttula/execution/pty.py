"""Low-level PTY and interactive shell abstraction for TTULA.

On Linux/Kali: Uses native POSIX `pty.openpty()`, sets non-blocking I/O,
and runs an interactive `bash` shell connected to the slave pty.
On Windows: Emulates a persistent interactive session via buffered subshell.
"""

from __future__ import annotations
import os
import sys
import time
import logging
from typing import Optional

logger = logging.getLogger("ttula.execution.pty")


class PTYSession:
    """Represents a low-level interactive terminal session."""

    def __init__(self, session_id: str, shell_cmd: Optional[str] = None):
        self.session_id = session_id
        self.shell_cmd = shell_cmd or ("bash" if os.name != "nt" else "cmd.exe")
        self.is_posix = os.name != "nt"
        self._master_fd: Optional[int] = None
        self._child_pid: Optional[int] = None
        self._proc = None
        self._output_queue = None
        self._alive = False

    def spawn(self) -> None:
        """Spawn the interactive shell."""
        if self.is_posix:
            self._spawn_posix()
        else:
            self._spawn_windows()
        self._alive = True

    def _spawn_posix(self) -> None:
        import pty
        import fcntl

        master_fd, slave_fd = pty.openpty()
        pid = os.fork()

        if pid == 0:
            # Child process
            os.close(master_fd)
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            if slave_fd > 2:
                os.close(slave_fd)

            os.environ["TERM"] = "xterm-256color"
            os.environ["PS1"] = f"ttula@{self.session_id}:$ "
            os.execlp(self.shell_cmd, self.shell_cmd, "--norc", "--noprofile")
            sys.exit(1)

        # Parent process
        os.close(slave_fd)
        # Set master_fd to non-blocking
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self._master_fd = master_fd
        self._child_pid = pid
        logger.info(f"POSIX PTY spawned for session {self.session_id} (pid={pid}, master_fd={master_fd})")

    def _spawn_windows(self) -> None:
        import subprocess
        import threading
        import queue

        cmd = ["cmd.exe", "/Q", "/K"]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._output_queue = queue.Queue()

        def reader():
            try:
                for line in iter(self._proc.stdout.readline, ""):
                    if self._output_queue is not None:
                        self._output_queue.put(line)
            except Exception:
                pass

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        logger.info(f"Windows fallback shell spawned for session {self.session_id}")

    def write(self, data: str) -> None:
        """Send input to the terminal session."""
        if not self.is_alive():
            raise RuntimeError(f"Session {self.session_id} is not alive.")

        if not data.endswith("\n"):
            data = data + "\n"

        if self.is_posix:
            os.write(self._master_fd, data.encode("utf-8"))
        else:
            if self._proc and self._proc.stdin:
                self._proc.stdin.write(data)
                self._proc.stdin.flush()

    def read(self, timeout: float = 0.3) -> str:
        """Read available output from the session up to timeout seconds."""
        if not self.is_alive():
            return ""

        if self.is_posix:
            return self._read_posix(timeout)
        else:
            return self._read_windows(timeout)

    def _read_posix(self, timeout: float) -> str:
        import select

        chunks = []
        end_time = time.time() + timeout
        while True:
            remaining = max(0.01, end_time - time.time())
            r, _, _ = select.select([self._master_fd], [], [], remaining)
            if not r:
                break
            try:
                chunk = os.read(self._master_fd, 4096)
                if not chunk:
                    break
                chunks.append(chunk.decode("utf-8", errors="replace"))
            except (OSError, BlockingIOError):
                break
            if time.time() >= end_time:
                break

        return "".join(chunks)

    def _read_windows(self, timeout: float) -> str:
        import queue

        chunks = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                line = self._output_queue.get(timeout=0.05)
                chunks.append(line)
            except queue.Empty:
                if chunks:
                    break
        return "".join(chunks)

    def is_alive(self) -> bool:
        if not self._alive:
            return False
        if self.is_posix:
            if self._child_pid:
                try:
                    pid, status = os.waitpid(self._child_pid, os.WNOHANG)
                    if pid != 0:
                        self._alive = False
                except OSError:
                    self._alive = False
        else:
            if self._proc and self._proc.poll() is not None:
                self._alive = False
        return self._alive

    def close(self) -> None:
        """Terminate and clean up session descriptors."""
        self._alive = False
        if self.is_posix:
            if self._master_fd is not None:
                try:
                    os.close(self._master_fd)
                except OSError:
                    pass
                self._master_fd = None
            if self._child_pid is not None:
                try:
                    os.kill(self._child_pid, 9)
                    os.waitpid(self._child_pid, 0)
                except OSError:
                    pass
                self._child_pid = None
        else:
            if self._proc:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None
        logger.info(f"Session {self.session_id} closed.")

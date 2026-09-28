"""Execution Manager for TTULA.

Manages persistent interactive PTY sessions and one-shot tool executions.
Implemented as a process-level singleton that survives Streamlit UI reruns.
"""

from __future__ import annotations
import uuid
import logging
from typing import Dict, List, Optional, Union
from ttula.core.models import Command, ExecutionNode, TerminalSession, ToolResult
from ttula.execution.pty import PTYSession
from ttula.execution.process import run_process_command

logger = logging.getLogger("ttula.execution.manager")


class ExecutionManager:
    """Process-level manager for interactive sessions and tool subprocesses."""

    _instance: Optional[ExecutionManager] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._pty_sessions: Dict[str, PTYSession] = {}
        self._session_records: Dict[str, TerminalSession] = {}
        self._command_count: Dict[str, int] = {}
        self._initialized = True
        logger.info("ExecutionManager singleton initialized.")

    def create_session(
        self,
        node: ExecutionNode,
        session_id: Optional[str] = None,
        shell_cmd: Optional[str] = None,
    ) -> TerminalSession:
        """Create and start a new interactive terminal session."""
        sid = session_id or f"session_{uuid.uuid4().hex[:8]}"
        if sid in self._pty_sessions and self._pty_sessions[sid].is_alive():
            return self._session_records[sid]

        pty = PTYSession(session_id=sid, shell_cmd=shell_cmd)
        pty.spawn()

        self._pty_sessions[sid] = pty
        self._command_count[sid] = 0

        session = TerminalSession(
            id=sid,
            node=node,
            pty_fd=getattr(pty, "_master_fd", None),
            alive=True,
        )
        self._session_records[sid] = session
        logger.info(f"Terminal session created: {sid} on node {node.name}")
        return session

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        session = self._session_records.get(session_id)
        if session and session_id in self._pty_sessions:
            session.alive = self._pty_sessions[session_id].is_alive()
        return session

    def list_sessions(self) -> List[TerminalSession]:
        for sid, sess in self._session_records.items():
            if sid in self._pty_sessions:
                sess.alive = self._pty_sessions[sid].is_alive()
        return list(self._session_records.values())

    def send(self, session_id: str, data: Union[str, List[str], Command]) -> None:
        """Send a command or string to an active terminal session."""
        pty = self._pty_sessions.get(session_id)
        if not pty or not pty.is_alive():
            raise RuntimeError(f"Session {session_id} not found or inactive.")

        if isinstance(data, Command):
            cmd_line = data.display_string
        elif isinstance(data, list):
            import shlex
            cmd_line = " ".join(shlex.quote(arg) for arg in data)
        else:
            cmd_line = str(data)

        pty.write(cmd_line)
        self._command_count[session_id] = self._command_count.get(session_id, 0) + 1
        if session_id in self._session_records:
            self._session_records[session_id].history.append(cmd_line)

    def read(self, session_id: str, timeout: float = 0.3) -> str:
        """Read pending output from an interactive session."""
        pty = self._pty_sessions.get(session_id)
        if not pty:
            return ""
        return pty.read(timeout=timeout)

    def get_command_count(self, session_id: str) -> int:
        return self._command_count.get(session_id, 0)

    def kill(self, session_id: str) -> None:
        """Kill a terminal session and free resources."""
        pty = self._pty_sessions.pop(session_id, None)
        if pty:
            pty.close()
        if session_id in self._session_records:
            self._session_records[session_id].alive = False
        logger.info(f"Session {session_id} killed.")

    def run_command(self, command: Command, timeout: float = 60.0) -> ToolResult:
        """Run a non-interactive command via subprocess."""
        return run_process_command(
            argv=command.argv,
            tool_name=command.source_tool,
            timeout=timeout,
        )

    def cleanup_all(self) -> None:
        """Clean up all active sessions (e.g. on shutdown)."""
        for sid in list(self._pty_sessions.keys()):
            self.kill(sid)


# Singleton getter
def get_execution_manager() -> ExecutionManager:
    return ExecutionManager()

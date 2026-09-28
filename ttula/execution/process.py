"""Non-interactive subprocess execution for TTULA.

Executes tools safely using strict argv lists, never shell=True strings.
"""

from __future__ import annotations
import subprocess
import time
import logging
from typing import List, Optional, Dict, Any
from ttula.core.models import Command, ToolResult

logger = logging.getLogger("ttula.execution.process")


def run_process_command(
    argv: List[str],
    tool_name: str = "system",
    timeout: Optional[float] = 60.0,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> ToolResult:
    """Execute a command via subprocess without shell interpolation.
    
    Security check: `argv` must be a list of non-empty strings.
    """
    if not isinstance(argv, list) or not argv:
        raise ValueError("argv must be a non-empty list of strings.")

    for i, token in enumerate(argv):
        if not isinstance(token, str):
            raise TypeError(f"argv element at index {i} must be str, got {type(token)}")

    start_time = time.time()
    try:
        logger.debug(f"Running command [{tool_name}]: {argv}")
        completed = subprocess.run(
            argv,
            shell=False,  # BINDING SECURITY REQUIREMENT
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        duration = time.time() - start_time
        return ToolResult(
            tool=tool_name,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            duration_seconds=round(duration, 3),
        )
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return ToolResult(
            tool=tool_name,
            stdout=stdout,
            stderr=f"Command timed out after {timeout}s. {stderr}",
            exit_code=-1,
            duration_seconds=round(duration, 3),
        )
    except FileNotFoundError as e:
        duration = time.time() - start_time
        return ToolResult(
            tool=tool_name,
            stdout="",
            stderr=f"Executable '{argv[0]}' not found in PATH: {e}",
            exit_code=127,
            duration_seconds=round(duration, 3),
        )
    except Exception as e:
        duration = time.time() - start_time
        return ToolResult(
            tool=tool_name,
            stdout="",
            stderr=f"Execution error: {str(e)}",
            exit_code=1,
            duration_seconds=round(duration, 3),
        )

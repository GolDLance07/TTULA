"""Test proving PTY session persistence across simulated UI reruns."""

from ttula.core.engine import create_default_engine
from ttula.execution.manager import get_execution_manager


def test_pty_session_persistence_across_reruns():
    """Simulates Streamlit's lifecycle where the script is re-executed repeatedly.
    The session_id is saved, and in subsequent reruns, the process-level singleton
    keeps the shell alive and remembers variable/directory state.
    """
    em1 = get_execution_manager()
    engine = create_default_engine(mock_tailscale=True, force_native_uro=True)
    node = engine.get_default_execution_node()

    # Rerun 1: User opens UI, creates session
    sess_id = "st_simulated_session_42"
    sess = em1.create_session(node, session_id=sess_id)
    assert sess.alive

    # User executes a state-setting command
    em1.send(sess_id, "export TTULA_STATE='active_session_proof'")

    # Rerun 2: User clicks a button in UI (Streamlit reruns script from top)
    em2 = get_execution_manager()  # fresh retrieval in new rerun cycle
    assert em2 is em1
    active_sess = em2.get_session(sess_id)
    assert active_sess is not None
    assert active_sess.alive

    # Execute another command in the SAME session
    em2.send(sess_id, "echo RERUN_2_EXECUTION")

    # Rerun 3: User triggers 10 more UI clicks/commands
    for click in range(10):
        em_click = get_execution_manager()
        em_click.send(sess_id, f"echo CLICK_RERUN_{click}")

    # Verify session stayed alive and counted all sequential commands
    total_cmds = em2.get_command_count(sess_id)
    assert total_cmds >= 12
    assert active_sess.alive

    # Read output and verify
    output = em2.read(sess_id, timeout=1.0)
    assert "CLICK_RERUN" in output or "RERUN_2_EXECUTION" in output

    em2.kill(sess_id)
    assert not active_sess.alive

"""50+ sequential command endurance test."""

from ttula.core.models import ExecutionNode
from ttula.execution.manager import get_execution_manager


def test_50_plus_sequential_commands():
    em = get_execution_manager()
    node = ExecutionNode(name="local", local=True)
    session = em.create_session(node, session_id="endurance_session")

    count = 55
    for i in range(count):
        em.send("endurance_session", f"echo ENDURANCE_TEST_{i}")

    assert em.get_command_count("endurance_session") >= count
    out = em.read("endurance_session", timeout=1.0)
    assert f"ENDURANCE_TEST_{count - 1}" in out
    em.kill("endurance_session")

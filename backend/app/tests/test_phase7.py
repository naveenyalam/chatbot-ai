"""
Phase 7 Test Suite — Agents, Calculator, Code Execution, Policy Enforcement, Model Router.
"""
import asyncio
import io
from PIL import Image
from app.tools.calculator import CalculatorTool
from app.tools.code_execution import CodeExecutionTool
from app.agents.policies import AgentPolicy
from app.agents.state import AgentState
from app.agents.manager import AgentManager
from app.services.model_router import ModelRouter
from app.core.errors import AgentStepLimitError, AgentTimeoutError
from app.core.config import settings
from datetime import datetime


# ─── Calculator Tests ────────────────────────────────────────────────────────

def test_calculator_basic():
    tool = CalculatorTool()

    def run(expr):
        return asyncio.run(tool.execute({"expression": expr}))

    r = run("2 + 2")
    assert r.success and r.data["result"] == "4"

    r = run("25 * 48")
    assert r.success and r.data["result"] == "1200"

    r = run("(10 + 5) * 2")
    assert r.success and r.data["result"] == "30"

    r = run("100 / 4")
    assert r.success and r.data["result"] == "25.0"


def test_calculator_advanced():
    tool = CalculatorTool()

    def run(expr):
        return asyncio.run(tool.execute({"expression": expr}))

    r = run("abs(-42)")
    assert r.success and r.data["result"] == "42"

    r = run("round(3.14159, 2)")
    assert r.success and r.data["result"] == "3.14"

    r = run("2 ** 10")
    assert r.success and r.data["result"] == "1024"

    r = run("max(1, 5, 3, 7, 2)")
    assert r.success and r.data["result"] == "7"


def test_calculator_security():
    """Verify the calculator cannot execute arbitrary Python."""
    tool = CalculatorTool()

    def run(expr):
        return asyncio.run(tool.execute({"expression": expr}))

    # These must ALL fail with an error
    dangerous = [
        "__import__('os').system('echo hacked')",
        "exec('import os')",
        "eval('1+1')",
        "open('/etc/passwd').read()",
        "print('hello')",  # not whitelisted
        "__builtins__",
    ]

    for expr in dangerous:
        r = run(expr)
        assert not r.success, f"Expected security rejection for: {expr!r}"


def test_calculator_zero_division():
    tool = CalculatorTool()
    r = asyncio.run(tool.execute({"expression": "1 / 0"}))
    assert not r.success
    assert "zero" in (r.error or "").lower()


# ─── Code Execution Tests ─────────────────────────────────────────────────────

def test_code_execution_simple():
    tool = CodeExecutionTool()
    r = asyncio.run(tool.execute({"language": "python", "code": "print('hello nova')"}))
    assert r.success
    assert "hello nova" in r.data["stdout"]


def test_code_execution_arithmetic():
    tool = CodeExecutionTool()
    r = asyncio.run(tool.execute({"language": "python", "code": "print(2 + 2)"}))
    assert r.success
    assert "4" in r.data["stdout"]


def test_code_execution_syntax_error():
    tool = CodeExecutionTool()
    r = asyncio.run(tool.execute({"language": "python", "code": "def broken(:\n    pass"}))
    assert not r.success
    assert r.data.get("stderr") or r.error


def test_code_execution_unsupported_language():
    tool = CodeExecutionTool()
    r = asyncio.run(tool.execute({"language": "javascript", "code": "console.log('hi')"}))
    assert not r.success
    assert "not supported" in (r.error or "").lower()


def test_code_execution_output_limit():
    tool = CodeExecutionTool()
    # Generate output larger than CODE_EXECUTION_MAX_OUTPUT
    big_code = f"print('A' * {settings.CODE_EXECUTION_MAX_OUTPUT + 5000})"
    r = asyncio.run(tool.execute({"language": "python", "code": big_code}))
    # Should succeed but output should be truncated
    assert len(r.data.get("stdout", "")) <= settings.CODE_EXECUTION_MAX_OUTPUT + 200


def test_code_execution_security_blocked():
    """Verify sandbox blocks dangerous operations."""
    tool = CodeExecutionTool()

    # os.system access should be blocked
    r = asyncio.run(tool.execute({
        "language": "python",
        "code": "import os\nos.system('echo hacked')"
    }))
    # RestrictedPython blocks imports — should fail
    # Either success=False or stdout should not contain 'hacked'
    if r.success:
        assert "hacked" not in r.data.get("stdout", "")


# ─── Agent Policy Tests ───────────────────────────────────────────────────────

def test_agent_policy_chat_allowed():
    assert AgentPolicy.can_use_tool("chat", "calculator") is True


def test_agent_policy_chat_blocked():
    # Chat agent must not access web_search
    assert AgentPolicy.can_use_tool("chat", "web_search") is False
    assert AgentPolicy.can_use_tool("chat", "code_execution") is False


def test_agent_policy_research_allowed():
    assert AgentPolicy.can_use_tool("research", "web_search") is True
    assert AgentPolicy.can_use_tool("research", "document_search") is True


def test_agent_policy_research_blocked():
    assert AgentPolicy.can_use_tool("research", "code_execution") is False
    assert AgentPolicy.can_use_tool("research", "calculator") is False


def test_agent_policy_task_all_tools():
    for tool in ["calculator", "web_search", "document_search", "code_execution"]:
        assert AgentPolicy.can_use_tool("task", tool) is True


def test_agent_step_limit_enforcement():
    state = AgentState(
        request_id="test-001",
        user_id="u1",
        conversation_id=None,
        mode="chat",
        messages=[],
        started_at=datetime.utcnow()
    )
    state.step = settings.MAX_AGENT_STEPS
    try:
        AgentPolicy.check_step_limit(state)
        assert False, "Should have raised AgentStepLimitError"
    except AgentStepLimitError:
        pass


# ─── Model Router Tests ───────────────────────────────────────────────────────

def test_model_router_fast():
    router = ModelRouter()
    model = router.get_model("fast")
    assert model == settings.AI_FAST_MODEL


def test_model_router_reasoning():
    router = ModelRouter()
    model = router.get_model("reasoning")
    assert model == settings.AI_REASONING_MODEL


def test_model_router_vision():
    router = ModelRouter()
    model = router.get_model("vision")
    assert model == settings.VISION_MODEL


def test_model_router_default_fallback():
    router = ModelRouter()
    model = router.get_model("nonexistent_purpose")
    assert model == settings.AI_MODEL


# ─── Agent Manager Integration Test ──────────────────────────────────────────

def test_agent_manager_chat_emits_text(monkeypatch):
    """Integration test: AgentManager must emit at least one text event for a chat request."""

    async def run():
        class MockDb:
            def add(self, x): pass
            def commit(self): pass
            def refresh(self, x): pass
            def query(self, *a): return self
            def filter(self, *a): return self
            def update(self, *a): pass

        async def mock_stream(*args, **kwargs):
            yield "4"

        monkeypatch.setattr("app.services.model_router.model_router.stream", mock_stream)

        manager = AgentManager()
        events = []
        async for event in manager.execute(
            request_id="test-req-001",
            user_id="user-test",
            conversation_id=None,
            messages=[{"role": "user", "content": "What is 2+2?"}],
            mode="normal",
            document_ids=[],
            model_alias=None,
            temperature=0.7,
            db=MockDb()
        ):
            events.append(event)

        return events

    events = asyncio.run(run())
    event_types = {e.get("type") for e in events}
    assert "text" in event_types, f"Expected text events, got: {event_types}"
